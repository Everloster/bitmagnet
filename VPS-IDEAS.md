# VPS 玩法 & 自托管服务灵感

> VPS: AWS EC2 us-west-2 | 创建日期: 2026-04-06
> 当前用途: WireGuard + wstunnel 为 bitmagnet DHT 爬虫提供网络出口

---

## 围绕 bitmagnet 生态

### *arr 全家桶自动追剧
- Prowlarr + Sonarr/Radarr 部署在 VPS 上
- 对接 bitmagnet 的 Torznab API 作为索引源
- 下载任务推送到本地 qBittorrent
- **价值**: 发现种子 → 匹配剧集 → 自动下载，全链路闭环

### 全文搜索增强
- VPS 上跑 Meilisearch 或 Typesense
- 给 bitmagnet 986 万条种子加一层快速搜索引擎
- 支持模糊匹配、中文分词、拼音搜索
- **价值**: 搜索体验从 PostgreSQL LIKE 提升到毫秒级

### 私有种子搜索前端
- 轻量 Web 前端 + Cloudflare Tunnel 暴露
- 给朋友提供一个私有种子搜索引擎
- **价值**: 不依赖公共站点，数据完全自控

---

## 网络基础设施

### 自建去广告 DNS
- AdGuard Home 或 Pi-hole 部署在 VPS
- 通过 WireGuard 隧道为本地设备提供 DNS
- 比 Clash 规则更底层，全设备生效
- **价值**: 系统级广告拦截 + DNS 隐私

### Tailscale/Headscale 组网
- 替代当前手工 WireGuard 配置
- Mac、VPS、手机组成 mesh VPN，任意设备间直连
- 自动处理 NAT 穿透、密钥轮换
- **价值**: 大幅简化网络配置，告别手工 iptables
- **优先级**: ⭐ 推荐优先考虑

### 反向代理统一入口
- Caddy 或 Traefik + 自动 HTTPS
- 一个域名通过子路径/子域名分发到不同自托管服务
- **价值**: 所有服务统一访问入口，自动证书管理

---

## 开发 & AI 相关

### 远程开发环境
- VPS 上跑 code-server 或 Claude Code
- 网络干净不受 Clash 影响
- 适合爬虫开发、API 调试等网络密集型任务
- **价值**: 绕过本地网络限制，开发体验更顺畅

### GitHub Actions Self-hosted Runner
- VPS 上装 GitHub Actions runner
- bitmagnet 的构建/测试跑在自己机器上
- 不限时、不排队、比 GitHub 免费 runner 快
- **价值**: CI/CD 自主可控
- **优先级**: ⭐ 对项目直接有帮助

### LLM API 网关
- 部署 one-api 或 new-api
- 统一管理 Claude/OpenAI 等模型的 API Key
- 限流、计费、多 Key 负载均衡
- 本地所有 AI 工具统一走这个入口
- **价值**: API Key 管理集中化，用量可视化

---

## 数据 & 监控

### Grafana 公网访问
- 通过 Cloudflare Tunnel 暴露 Grafana 面板
- 手机上随时查看 bitmagnet 爬取状态和系统指标
- **价值**: 移动端监控

### 数据库定时备份
- VPS 上 cron 定期 pg_dump bitmagnet 数据库
- 推送到 S3 或 Cloudflare R2
- 986 万条数据丢了重新爬需要很久
- **价值**: 数据安全保障
- **优先级**: ⭐ 强烈推荐

### Uptime Kuma 服务监控
- 监控所有自托管服务的可用性
- 挂了发 Telegram / 微信 / Bark 通知
- **价值**: 第一时间知道服务异常

---

## 好玩的

### RSS 聚合阅读
- Miniflux 或 FreshRSS
- VPS 抓 RSS 不受墙限制
- 配合 Reeder 等客户端阅读
- **价值**: 信息获取不受网络限制

### 个人知识库
- Outline / Memos / Wiki.js
- 技术笔记、项目文档、学习记录
- **价值**: 比本地 Markdown 多了搜索和多端访问

### 自建密码管理器
- Vaultwarden（Bitwarden 兼容）
- 完全自托管，数据在自己手里
- 支持浏览器扩展和移动端
- **价值**: 密码安全自主可控

---

## 优先级建议

| 优先级 | 项目 | 理由 |
|--------|------|------|
| ⭐⭐⭐ | 数据库定时备份 | 数据无价，防丢失 |
| ⭐⭐⭐ | Tailscale 组网 | 简化当前 WireGuard 痛点 |
| ⭐⭐ | GitHub Actions Runner | 提升开发效率 |
| ⭐⭐ | *arr 追剧全家桶 | bitmagnet 生态闭环 |
| ⭐ | 其余项目 | 按兴趣和需求逐步折腾 |
