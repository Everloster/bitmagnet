# Bitmagnet 维护与优化计划

> Fork 日期：2026-04-05 | 维护者：Claude (AI Agent)  
> 目标：自用 DHT 搜索引擎 + 爬虫性能提升 + 中文内容优化

---

## 执行规则

- 每完成一个任务后，等待确认再进行下一个
- 每个任务包含：目标、改动文件、验证方式
- 状态标记：`[ ]` 待做 / `[→]` 进行中 / `[x]` 已完成 / `[~]` 跳过

---

## Phase 0：安全检查

### Task 0.1 — 确认 .env 凭证未泄漏到 git history
- **目标**：检查历史 commit 中是否含有 `.env` 内容或明文凭证
- **操作**：`git log --all -- .env`，扫描历史提交内容
- **验证**：无 `.env` 相关 commit 记录
- **状态**：`[x]` 已完成（git history 中无 .env 提交记录，安全）

---

## Phase 1：可观测性 — 接入 Prometheus + Grafana

### Task 1.1 — 在 docker-compose.yml 添加监控服务
- **目标**：添加 Prometheus、Grafana、postgres-exporter 三个服务
- **改动文件**：`docker-compose.yml`
- **新增服务**：
  - `prometheus`：使用已有的 `observability/prometheus.config.yaml`
  - `grafana`：使用已有的 `observability/grafana.datasources.yaml` + `grafana.dashboards.yaml` + `grafana-dashboards/bitmagnet.json`
  - `postgres-exporter`：暴露 PostgreSQL 指标给 Prometheus 采集
- **验证**：`docker compose up -d`，访问 http://localhost:3000 查看 Grafana 仪表板
- **状态**：`[ ]`

### Task 1.2 — 确认 Grafana 仪表板显示爬虫指标
- **目标**：验证 Grafana 能正确显示 `bitmagnet_dht_crawler_persisted_total` 等指标
- **操作**：打开 Grafana → Dashboards → Bitmagnet，观察数据是否正常
- **验证**：至少能看到 DHT 路由表节点数、metainfo 请求指标
- **状态**：`[ ]`

---

## Phase 2：爬虫性能调优

### Task 2.1 — 提升 ScalingFactor 并观察效果
- **目标**：将爬虫并发度从默认 10 提升到 15
- **改动文件**：`.env`
- **变更内容**：
  ```
  BITMAGNET_DHT_CRAWLER_SCALING_FACTOR=15
  ```
- **影响**：
  - `requestMetaInfo` goroutine：400 → 600
  - `nodesForFindNode` / `SampleInfoHashes`：各 100 → 150 goroutine
- **验证**：重启容器，10 分钟后对比 `torrents` 表入库速率
- **状态**：`[ ]`

### Task 2.2 — 增加 Bootstrap 节点
- **目标**：增加 2 个额外的 DHT bootstrap 节点，加速节点发现
- **改动文件**：`docker-compose.yml`（环境变量 `BITMAGNET_DHT_CRAWLER_BOOTSTRAP_NODES`）
- **新增节点**：`dht.libtorrent.org:25401`、`router.silotis.us:6881`
- **验证**：查看 `bitmagnet_dht_ktable_nodes_count` 指标，节点数应有提升
- **状态**：`[ ]`

### Task 2.3 — 根据监控调整 Metainfo 速率限制（可选）
- **目标**：如果发现 `bitmagnet_meta_info_requester_error_total` 很低，考虑放宽速率
- **改动文件**：`internal/protocol/metainfo/metainforequester/factory.go`
- **前提**：需要先运行 1 周，根据实际错误率决定是否调整
- **状态**：`[ ]`（待观察后决定）

---

## Phase 3：中文内容分类优化

### Task 3.1 — 了解并记录现有分类器规则
- **目标**：读取现有 classifier 配置，了解默认分类规则
- **改动文件**：无（只读）
- **操作**：阅读 `internal/classifier/` 下的规则文件和默认配置
- **验证**：能够描述当前对中文内容的识别能力和盲区
- **状态**：`[ ]`

### Task 3.2 — 扩充中文影视关键词组
- **目标**：添加中文视频常见标签（国语、粤语、中字、简繁中文等）到分类器关键词组
- **改动文件**：classifier 配置文件（待 Task 3.1 后确认具体路径）
- **验证**：搜索含中文标签的种子，确认分类正确
- **状态**：`[ ]`

### Task 3.3 — 验证 TMDB 中文元数据效果
- **目标**：确认 TMDB API 为中文电影/剧集返回正确的中文标题和元数据
- **操作**：手动触发几个中文影视 hash 的重新分类，观察结果
- **验证**：GraphQL 查询 `torrentContent { search }` 返回中文标题
- **状态**：`[ ]`

---

## Phase 4：功能扩展（按需，后续规划）

### Task 4.1 — Torznab + qBittorrent 集成
- **目标**：通过 Torznab 接口与 qBittorrent 自动下载集成
- **状态**：`[ ]`（待 Phase 1-3 稳定后）

### Task 4.2 — 定期数据备份脚本
- **目标**：添加 PostgreSQL 定时备份到本地
- **状态**：`[ ]`

### Task 4.3 — GraphQL API 扩展
- **目标**：按需添加自定义查询接口
- **状态**：`[ ]`

---

## 快速参考

### 查看当前入库速率
```bash
docker exec bitmagnet-postgres psql -U postgres bitmagnet \
  -c "SELECT count(*) FROM torrents;"
```

### 查看爬虫日志
```bash
docker compose logs bitmagnet -f --tail=50
```

### 重启并重建
```bash
docker compose up -d --build
```

### 关键性能参数位置
| 参数 | 文件 | 环境变量 |
|------|------|---------|
| 并发度乘数 | `internal/dhtcrawler/config.go` | `BITMAGNET_DHT_CRAWLER_SCALING_FACTOR` |
| Metainfo 超时 | `internal/protocol/metainfo/metainforequester/config.go` | `BITMAGNET_METAINFO_REQUESTER_REQUEST_TIMEOUT` |
| Bootstrap 节点 | `internal/dhtcrawler/config.go` | `BITMAGNET_DHT_CRAWLER_BOOTSTRAP_NODES` |
| 最大文件数 | `internal/dhtcrawler/config.go` | `BITMAGNET_DHT_CRAWLER_SAVE_FILES_THRESHOLD` |
