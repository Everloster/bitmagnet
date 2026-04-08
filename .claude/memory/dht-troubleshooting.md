---
name: dht-troubleshooting
description: BitMagnet DHT 爬虫故障排查经验总结
type: project
---

# DHT 实战排查经验（2026-04-06）

> 基于 BitMagnet DHT 爬虫真实故障，串联 DHT/Kademlia 协议理论、网络隧道架构、分层诊断方法论。

## 系统架构

```
bitmagnet (Go, UDP:3334)
    → gluetun (WireGuard 客户端, tun0)
    → wstunnel 客户端 (UDP:51820 → WebSocket TCP:8080)
    → Docker Desktop VPNKit → macOS Clash Verge TUN
    → VPS wstunnel 服务端 (TCP:8080 → UDP:51820)
    → WireGuard 服务端 (UDP:51820) → 公网 IP 出口
```

**核心矛盾**：DHT 是 UDP 协议，而 Docker Desktop VPNKit 对 UDP 支持有限，所以用 wstunnel 将 UDP 封装进 WebSocket（TCP）。

## 排查方法论：分层诊断

从最内层开始，逐层向外验证：

1. VPS 服务检查（进程、端口监听）
2. VPS 本地回环（curl 127.0.0.1）
3. 外部 → VPS 连通性（tcpdump 确认数据包是否真正到达）
4. Docker → VPS（容器网络测试）
5. WireGuard 隧道（wg show 统计）
6. 端到端 DHT 功能（发送真实 bencode PING）

**关键工具**：`tcpdump` 是最可靠的手段，不依赖应用层协议。

## 故障遮蔽

两个独立根因可能同时出现，修复第一个后第二个才暴露：
- 根因 1：AWS 安全组未开放 TCP 8080 → wstunnel 握手失败
- 根因 2：DHT bootstrap 节点大面积失效 → 隧道通但 DHT 仍 down

## DHT Bootstrap 节点现状（2026-04 实测）

| 节点 | 状态 |
|------|------|
| `router.bittorrent.com:6881` | **死亡** |
| `router.utorrent.com:6881` | **死亡** |
| `dht.transmissionbt.com:6881` | 存活 |
| `dht.libtorrent.org:25401` | 存活 |
| `dht.aelitis.com:6881` | **死亡** |
| `router.silotis.us:6881` | **DNS 解析失败** |

6 个主流节点仅 2 个存活（33%）。建议自建 bootstrap 节点。

## 代理环境陷阱

| 现象 | 真实情况 |
|------|----------|
| curl 显示 "Connected" | 代理在本地完成握手，目标端 tcpdump 验证 |
| TCP 通但 UDP 不通 | Docker Desktop VPNKit UDP 限制，用 wstunnel 封装 |
| DNS 正常但连接超时 | 安全组/防火墙阻止端口 |
| 隧道通但应用不工作 | 应用层问题（如 bootstrap 节点失效） |

## 敏感信息管理

docker-compose.yml 中所有密钥、IP 必须用 `${ENV_VAR}` 引用。`.gitignore` 需包含：
- `*.pem`
- `wireguard/`
- `wg0.conf`
- `.env`

## 相关文档

- `DHT实战排查：从协议理论到工程故障诊断.md`
- `WSTUNNEL-WSS-MIGRATION.md`
