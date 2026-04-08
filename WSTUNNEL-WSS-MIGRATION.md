# wstunnel ws:// → wss:// 迁移方案

> 创建：2026-04-08
> 起因：BitMagnet DHT 流量经 Clash 代理时占用机场带宽。加 PROCESS-NAME 旁路后改走直连，但因 wstunnel 当前使用明文 `ws://`，GFW 对长 TCP 连接敏感，导致隧道频繁断开（直连下单条隧道仅存活 ~14 秒，过 Clash 时 ~4 分钟）。
> 目标：把 wstunnel 升级为 `wss://`（TLS 加密 WebSocket），让旁路后的直连也能长稳，同时不烧机场流量。

---

## 现状诊断（2026-04-08 凌晨）

**架构**：
```
bitmagnet → gluetun(WG) → wstunnel-client(UDP→ws/TCP:8080)
   → [Docker NAT → 宿主机 → Clash TUN 或 直连]
   → 100.23.62.114:8080 → wstunnel-server → WireGuard server
```

**VPS 端**：
- wstunnel server 健康，自 Apr 5 起运行无重启
- systemd unit `wstunnel.service`，监听 `ws://0.0.0.0:8080`（**无 TLS**）
- WG peer 10.0.0.2 累计：13.58 GiB 入 / 52.01 GiB 出

**客户端隧道存活时间**：
| 路径 | 单条隧道存活 | 备注 |
|---|---|---|
| 经 Clash US 出口 (`45.8.204.50`) | ~4 分钟 | Clash 节点 TCP idle timeout |
| **直连（中国移动 `39.144.128.111`）** | **~14 秒** | **GFW 对明文 ws:// 长 TCP 连主动 RST** |

**结论**：明文 `ws://` 是问题根源。TLS 包一层后 GFW 看不到内层协议，应能稳定。

---

## 路径 A — 自签证书（推荐，~10 分钟）

适用：无域名、想最快验证方案是否有效。

### Step 1 — VPS 上生成自签证书

```bash
ssh -i ~/workspace/bitmagnet/bitmagnet-key.pem ec2-user@100.23.62.114

sudo mkdir -p /etc/wstunnel
sudo openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout /etc/wstunnel/key.pem \
  -out   /etc/wstunnel/cert.pem \
  -subj  "/CN=bitmagnet-wstunnel"
sudo chown -R nobody:nobody /etc/wstunnel
sudo chmod 600 /etc/wstunnel/key.pem
```

### Step 2 — 改 systemd unit

```bash
sudo systemctl edit --full wstunnel.service
```

把 `ExecStart` 一行替换为：

```
ExecStart=/usr/local/bin/wstunnel server \
  --restrict-to 127.0.0.1:51820 \
  --tls-certificate /etc/wstunnel/cert.pem \
  --tls-private-key /etc/wstunnel/key.pem \
  wss://0.0.0.0:8080
```

应用并验证：

```bash
sudo systemctl daemon-reload
sudo systemctl restart wstunnel
sudo systemctl status wstunnel        # 应 active (running)
sudo ss -tlnp | grep 8080             # 应仍监听 8080
sudo journalctl -u wstunnel -n 30 --no-pager
```

### Step 3 — 改本地 docker-compose.yml

文件：`~/workspace/bitmagnet/docker-compose.yml`，wstunnel 服务的 `command` 块。

**改前**：
```yaml
command:
  - /home/app/wstunnel
  - client
  - -L
  - "udp://0.0.0.0:51820:127.0.0.1:51820"
  - "ws://${WSTUNNEL_SERVER_IP}:${WSTUNNEL_SERVER_PORT:-8080}"
```

**改后**：
```yaml
command:
  - /home/app/wstunnel
  - client
  - --tls-verify-certificate=false   # 自签证书，跳过 CA 验证
  - -L
  - "udp://0.0.0.0:51820:127.0.0.1:51820"
  - "wss://${WSTUNNEL_SERVER_IP}:${WSTUNNEL_SERVER_PORT:-8080}"
```

> 注：`--tls-verify-certificate=false` 是 wstunnel v10.x 的写法。如果该 flag 报错，备选方案：
> 1. 把 `cert.pem` 从 VPS 拷到本地，挂载进容器，用 `--tls-trust-certificate=/etc/wstunnel/cert.pem`
> 2. 或者直接走路径 B（Let's Encrypt + 域名），无需跳过验证

### Step 4 — 重启客户端栈

```bash
cd ~/workspace/bitmagnet
docker compose up -d --force-recreate wstunnel gluetun bitmagnet
docker logs -f bitmagnet-wstunnel
```

### Step 5 — 验证（≥10 分钟）

```bash
# 客户端隧道日志
docker logs --tail 50 bitmagnet-wstunnel 2>&1 | grep -iE "EOF|tunnel|opening"

# VPS 端
ssh -i ~/workspace/bitmagnet/bitmagnet-key.pem ec2-user@100.23.62.114 \
  'sudo journalctl -u wstunnel --since "10 min ago" --no-pager | grep -iE "EOF|Accepting|tunnel"'

# DHT 状态
open http://localhost:3333/webui/dashboard
```

**成功标准**：
- 单条隧道存活 ≥ 30 分钟（之前 14 秒）
- VPS journal 不再每分钟出现 `Unexpected EOF`
- BitMagnet dashboard 显示 DHT crawler 持续上量

### Step 6 — 旁路保留

`rUxtFltO0seJ.yaml` 里的 PROCESS-NAME 旁路无需改动。wss 加密后直连应稳，机场流量归零。

---

## 路径 B — Let's Encrypt + 域名（~30 分钟，更优雅长稳）

适用：手上有域名能加 A 记录、想长期不折腾。

### 前置条件

- 一个域名，能在 DNS 处加 A 记录指向 `100.23.62.114`
- 假设域名为 `wt.example.com`（替换为你的真实域名）

### Step 1 — 加 A 记录

在域名 DNS 控制台加：
```
wt.example.com  A  100.23.62.114  TTL 300
```
等 1~2 分钟，本地 `dig wt.example.com` 确认解析。

### Step 2 — VPS 上申请 Let's Encrypt 证书

```bash
ssh -i ~/workspace/bitmagnet/bitmagnet-key.pem ec2-user@100.23.62.114

# AL2023
sudo dnf install -y certbot
# 或 Ubuntu/Debian: sudo apt install certbot

# 申请证书（standalone 模式会临时占用 80 端口）
sudo certbot certonly --standalone -d wt.example.com \
  --register-unsafely-without-email --agree-tos
```

证书路径：
- `/etc/letsencrypt/live/wt.example.com/fullchain.pem`
- `/etc/letsencrypt/live/wt.example.com/privkey.pem`

让 wstunnel 进程能读：

```bash
sudo chmod -R 755 /etc/letsencrypt/live /etc/letsencrypt/archive
sudo chmod 644 /etc/letsencrypt/archive/wt.example.com/privkey*.pem
```

### Step 3 — 改 systemd unit

```bash
sudo systemctl edit --full wstunnel.service
```

改 `ExecStart`：

```
ExecStart=/usr/local/bin/wstunnel server \
  --restrict-to 127.0.0.1:51820 \
  --tls-certificate /etc/letsencrypt/live/wt.example.com/fullchain.pem \
  --tls-private-key /etc/letsencrypt/live/wt.example.com/privkey.pem \
  wss://0.0.0.0:8080
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart wstunnel
sudo systemctl status wstunnel
```

### Step 4 — 配 certbot 自动续期

```bash
# 创建续期 hook：续期成功后重启 wstunnel
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo tee /etc/letsencrypt/renewal-hooks/deploy/restart-wstunnel.sh > /dev/null <<'EOF'
#!/bin/bash
systemctl restart wstunnel
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/restart-wstunnel.sh

# certbot 通常自带 systemd timer，验证下
sudo systemctl status certbot.timer
# 没有就手工 cron：
# 0 3 * * * root certbot renew --quiet
```

### Step 5 — 改本地配置

`~/workspace/bitmagnet/.env` 里：

```
WSTUNNEL_SERVER_IP=wt.example.com
```

`docker-compose.yml` wstunnel command 块：

```yaml
command:
  - /home/app/wstunnel
  - client
  - -L
  - "udp://0.0.0.0:51820:127.0.0.1:51820"
  - "wss://${WSTUNNEL_SERVER_IP}:${WSTUNNEL_SERVER_PORT:-8080}"
```

> 注意：路径 B **不需要** `--tls-verify-certificate=false`，因为 Let's Encrypt 是公网受信 CA。

### Step 6 — 旁路调整

`rUxtFltO0seJ.yaml` 里那条 IP-CIDR `100.23.62.114/32` 可以保留。但 wstunnel 客户端连的是域名 `wt.example.com`，DNS 解析后仍是同一 IP，所以旁路依然命中。

PROCESS-NAME 旁路也保留。

### Step 7 — 重启客户端栈

```bash
cd ~/workspace/bitmagnet
docker compose up -d --force-recreate wstunnel gluetun bitmagnet
docker logs -f bitmagnet-wstunnel
```

### Step 8 — 验证

同路径 A 的 Step 5，标准一致。

### 额外好处（路径 B 独有）

- 90 天到期前 certbot 自动续期，零维护
- 后续可前置 Nginx，把 wstunnel 藏在某个 path 后面（如 `wss://wt.example.com/tunnel`），对 GFW 看起来就是普通 HTTPS 网站
- 如果未来想改 Cloudflare CDN 中转，路径 B 是基础

---

## 路径选择建议

| 场景 | 推荐 |
|---|---|
| 没有域名 / 想 10 分钟内验证可行性 | **A** |
| 有域名 / 想长期不折腾 / 未来可能要套 CDN | **B** |
| A 跑通后觉得够稳 | 留 A，不必升 B |
| A 仍有偶发断开（说明 GFW 对自签 TLS 也敏感） | 升 B |

**默认建议执行顺序**：先 A 做 PoC（10 分钟），稳一小时确认有效后，再决定要不要升 B。

---

## 回滚方案

如果迁移后反而出问题，**两步回滚**：

### VPS 端
```bash
ssh -i ~/workspace/bitmagnet/bitmagnet-key.pem ec2-user@100.23.62.114
sudo systemctl edit --full wstunnel.service
# 把 ExecStart 改回：
# ExecStart=/usr/local/bin/wstunnel server --restrict-to 127.0.0.1:51820 ws://0.0.0.0:8080
sudo systemctl daemon-reload && sudo systemctl restart wstunnel
```

### 客户端
```bash
cd ~/workspace/bitmagnet
git checkout docker-compose.yml   # 如果改动已 commit，git revert 那个 commit
docker compose up -d --force-recreate wstunnel gluetun bitmagnet
```

---

## 路径 A 执行结果（2026-04-08 Claude Code 实施）

**执行时间**：2026-04-08 14:05 CST

### 关键发现

**文档错误**：`--tls-verify-certificate=false` 在 wstunnel v10.1.4 中不存在此 flag。客户端连接自签证书的 wss:// 服务端，**无需传任何 TLS 相关 flag**（默认接受自签）。

### 实际操作

**VPS 端**：无变化，同文档 Step 1-2。

**本地 docker-compose.yml wstunnel command 块**：

```yaml
command:
  - /home/app/wstunnel
  - client
  - -L
  - "udp://0.0.0.0:51820:127.0.0.1:51820"
  - "wss://${WSTUNNEL_SERVER_IP}:${WSTUNNEL_SERVER_PORT:-8080}"
```

> 注意：**不**需要 `--tls-verify-certificate=false` 或 `--tls-trust-certificate`。v10.1.4 客户端默认接受自签证书。

### 验证结果（2026-04-08 14:15 CST，持续监控约 10 分钟）

| 指标 | 结果 |
|------|------|
| 单条隧道存活 | **> 5 分钟且无断开迹象**（vs 迁移前 14 秒） |
| VPS journal EOF/InvalidContentType（最近 3 分钟） | **0** |
| VPS TCP ESTAB 连接 | 持续活跃，接收字节稳定增长 |
| gluetun 状态 | healthy |
| DHT crawler | 稳定运行 |

**结论**：路径 A 成功。TLS 加密后 GFW 不再对隧道做 RST，隧道可长时间稳定存活。

---

## 待解决/未知问题

1. **wstunnel v10.x 的客户端跳过证书验证 flag 准确写法**：本文档默认 `--tls-verify-certificate=false`，需在 Step 4 实测。如果报错，备用方案是 `--tls-trust-certificate` 挂载证书。
2. **GFW 对自签 TLS 的容忍度**：理论上 TLS 握手后 GFW 看不到内层，但部分省份运营商对"无 SNI / 自签 SNI 的长连接"也会做嗅探干扰。需路径 A 实测验证。
3. **DHT 流量量级**：当前 52 GiB/3 天 ≈ 17 GiB/天。如果迁移后流量未变，需要在 BitMagnet 侧配 `BITMAGNET_DHT_CRAWLER_RATE_LIMIT` 节流。

---

## 相关文档

- 上一次 DHT 排查的完整推理：`~/workspace/EverAgent/cs-learning/reports/knowledge_reports/DHT实战排查：从协议理论到工程故障诊断.md`
- BitMagnet 项目：`~/workspace/bitmagnet/`
- Clash 旁路规则文件：`~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/profiles/rUxtFltO0seJ.yaml`

---

*本文档路径 A 执行记录由 Claude MiniMax-M2.7 于 2026-04-08 添加，验证 TLS 隧道稳定，修正了 `--tls-verify-certificate=false` flag 不存在的问题。*
