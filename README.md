# Bitmagnet

自托管 BitTorrent 索引器、DHT 爬虫、内容分类器和种子搜索引擎。

## 特性

- **DHT 爬虫** - 从 BitTorrent DHT 网络发现和爬取种子
- **内容分类** - 自动识别电影、剧集、音乐、图书、有声书等
- **GraphQL API** - 强大的搜索和过滤 API，支持复杂查询
- **Torznab 集成** - 与 Sonarr、Radarr、Prowlarr 无缝集成
- **Web UI** - 友好的浏览器界面，支持多语言

## 技术栈

- Go 1.23.6
- Angular 18 (WebUI)
- PostgreSQL 16
- GraphQL (gqlgen)

## 本地运行

### 1. 启动 PostgreSQL

```bash
brew services start postgresql@16
```

### 2. 创建数据库

```bash
createuser -s postgres
createdb -O postgres bitmagnet
```

### 3. 编译

```bash
go build -o bitmagnet .
```

### 4. 运行

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PASSWORD=postgres
export BITMAGNET_POSTGRES="postgres://postgres:postgres@localhost:5432/bitmagnet?sslmode=disable"

./bitmagnet worker run --keys=http_server --keys=queue_server --keys=dht_crawler
```

### 5. 访问

- WebUI: http://localhost:3333/webui/
- GraphQL API: http://localhost:3333/graphql

## Docker 部署（VPN 模式）

通过 WireGuard + wstunnel 让 DHT 流量走 VPS 出口，适用于本地网络环境受限的场景（如 macOS + 代理软件）。

### 架构

```
bitmagnet ──(network_mode)──► gluetun (WireGuard) ──► wstunnel client ──ws──► VPS:wstunnel server ──► WireGuard server ──► Internet
```

### 前置条件

1. 一台公网 VPS，安装 WireGuard 和 wstunnel server
2. VPS 安全组/防火墙开放：TCP 8080（wstunnel）、UDP 51820（WireGuard 备用）、UDP+TCP 3334（DHT 入站）
3. VPS 配置 iptables 端口转发，将 3334 流量 DNAT 到 WireGuard 客户端

### 启动

```bash
cp .env.example .env
# 编辑 .env，填入 WireGuard 密钥和 VPS IP
docker compose up -d
```

### VPS 端 wstunnel server

```bash
wstunnel server --restrict-to 127.0.0.1:51820 ws://0.0.0.0:8080
```

### VPS 端口转发（WireGuard PostUp 中配置）

```bash
iptables -t nat -A PREROUTING -i <iface> -p udp --dport 3334 -j DNAT --to-destination 10.0.0.2:3334
iptables -t nat -A PREROUTING -i <iface> -p tcp --dport 3334 -j DNAT --to-destination 10.0.0.2:3334
iptables -A FORWARD -i <iface> -o wg0 -p udp --dport 3334 -j ACCEPT
iptables -A FORWARD -i <iface> -o wg0 -p tcp --dport 3334 -j ACCEPT
```

## 项目结构

```
├── main.go              # 入口文件
├── internal/            # 核心代码
│   ├── app/             # 应用入口和 CLI
│   ├── classifier/       # 内容分类器 (CEL 规则引擎)
│   ├── dhtcrawler/      # DHT 爬虫
│   ├── database/        # 数据库层 (GORM)
│   ├── gql/             # GraphQL API
│   ├── queue/           # 队列管理
│   ├── torznab/         # Torznab 协议
│   └── worker/          # Worker 系统
├── graphql/             # GraphQL schema 定义
├── migrations/          # 数据库迁移
└── webui/              # Angular 前端
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_HOST` | 数据库地址 | localhost |
| `POSTGRES_PASSWORD` | 数据库密码 | postgres |
| `BITMAGNET_POSTGRES` | PostgreSQL 连接字符串 | - |
| `TMDB_API_KEY` | TMDB API Key（可选） | - |
| `WIREGUARD_PRIVATE_KEY` | WireGuard 客户端私钥（Docker VPN 模式） | - |
| `WIREGUARD_PUBLIC_KEY` | WireGuard 服务端公钥（Docker VPN 模式） | - |
| `WSTUNNEL_SERVER_IP` | wstunnel 服务端 IP（Docker VPN 模式） | - |
| `WSTUNNEL_SERVER_PORT` | wstunnel 服务端端口 | 8080 |
| `DHT_CRAWLER_BOOTSTRAP_NODES` | DHT 引导节点列表（可选） | 见 docker-compose.yml |

### Worker

- `http_server` - HTTP 服务器和 WebUI
- `queue_server` - 队列服务器
- `dht_crawler` - DHT 爬虫

使用 `--all` 启动所有 worker，或使用 `--keys` 指定特定 worker。

## License

MIT

---

本项目 fork 自 [bitmagnet-io/bitmagnet](https://github.com/bitmagnet-io/bitmagnet)，将遵守其 MIT 协议。
