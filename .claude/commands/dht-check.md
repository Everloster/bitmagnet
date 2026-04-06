---
description: "搜索、发现并验证 DHT Bootstrap 节点的可用性"
---

# DHT Bootstrap Node Check

你是 DHT Bootstrap 节点检查工具。按以下流程执行：

## 步骤 1：搜索发现新节点

使用 WebSearch 和 WebFetch 工具搜索新的 DHT bootstrap 节点：

1. 搜索 GitHub 上主流 BitTorrent 客户端的 bootstrap 节点配置：
   - `github.com/anacrolix/dht` (Go DHT library)
   - `github.com/transmission/transmission` (Transmission)
   - `github.com/qbittorrent/qBittorrent` (qBittorrent)
   - `github.com/arvidn/libtorrent` (libtorrent)
   - `github.com/webtorrent/bittorrent-dht` (Node.js DHT)
2. 搜索关键词：`DHT bootstrap nodes list 2025 2026`
3. 收集所有发现的 host:port 对

## 步骤 2：合并到 JSON

读取 `dht-check/dht-bootstrap-nodes.json`，将新发现的节点添加进去（去重），source 设为搜索来源。

## 步骤 3：验证��用性

运行验证脚本，优先通过 VPS SSH 验证：

```bash
python3 dht-check/verify.py
```

如果 VPS 不可达，回退到本地验证：

```bash
python3 dht-check/verify.py --local
```

## 步骤 4：输出报告

1. 展示验证结果（存活/死亡节点列表）
2. 给出建议的 `DHT_CRAWLER_BOOTSTRAP_NODES` 值
3. 检查 `dht-check/dht-bootstrap-nodes.json` 中的 `auto_update_env` 字段：
   - 如果为 `true`：自动更新 `.env` 中的 `DHT_CRAWLER_BOOTSTRAP_NODES` 并提示用户重启 bitmagnet
   - 如果为 `false`（默认）：只展示建议值，由用户决定是否更新

## 注意事项

- 节点验证优先通过 VPS SSH（结果更准确，不受本地代理影响）
- 所有结果写入 `dht-check/dht-bootstrap-nodes.json` 以便追踪历史
- 域名节点比 IP 节点��优先推荐（域名可以更换后端 IP）
- 不要删除 json 中已有的节点，即使状态为 dead（保留历史记录）
