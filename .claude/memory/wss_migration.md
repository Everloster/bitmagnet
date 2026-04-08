---
name: wss-migration
description: wstunnel ws:// → wss:// 迁移记录及后续维护信息
type: project
---

# wstunnel wss:// 迁移（2026-04-08）

## 当前状态

**已完成**：wstunnel 客户端从 `ws://` 迁移到 `wss://`，隧道稳定。

## 关键发现（重要）

wstunnel v10.1.4 客户端连接自签证书的 `wss://` 服务端，**无需任何 TLS flag**：
- `--tls-verify-certificate=false` 不存在
- `--tls-trust-certificate` 是**服务端**参数，客户端不需要
- 客户端默认接受自签证书

## 密钥/证书位置

- **VPS 自签证书**：`/etc/wstunnel/cert.pem`（公钥）, `key.pem`（私钥）
  - 有效期 10 年（3650 天），2048 RSA
  - CN=bitmagnet-wstunnel
  - 续期需在 VPS 上重新生成并 `systemctl restart wstunnel`
- **本地**：不需要证书
- **SSH 私钥**：`~/workspace/bitmagnet/bitmagnet-key.pem`（gitignore）

## 配置文件

- `docker-compose.yml`：wstunnel command 已改为 `wss://${WSTUNNEL_SERVER_IP}:...`
- VPS systemd unit：`/etc/systemd/system/wstunnel.service` 已改为 `wss://0.0.0.0:8080`

## 后续其他 Agent 维护提示

1. **不要传 `--tls-verify-certificate=false`**：此 flag 在 v10 中不存在，客户端默认接受自签
2. **VPS 证书续期**：自签证书 10 年，到期前在 VPS 上重新生成即可
3. **如需升级 Let's Encrypt（路径 B）**：参考 `WSTUNNEL-WSS-MIGRATION.md` 路径 B 章节
4. **隧道断开排查**：先查 VPS `journalctl -u wstunnel`，再看 `sudo ss -tpn | grep wstunnel`

## 相关信息

- 完整迁移文档：`/Users/jabe/workspace/bitmagnet/WSTUNNEL-WSS-MIGRATION.md`
- DHT 排查文档：`/Users/jabe/workspace/bitmagnet/DHT实战排查：从协议理论到工程故障诊断.md`
