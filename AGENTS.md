# Bitmagnet — AI 协作规范

> 本项目 fork 自 [bitmagnet-io/bitmagnet](https://github.com/bitmagnet-io/bitmagnet)，遵守 MIT 协议。

---

## 1. Git 初始化

```bash
# 设置远程仓库（使用 .env 中的 TOKEN）
GITHUB_TOKEN=$(grep GITHUB_TOKEN .env | cut -d'"' -f2)
git remote set-url origin https://${GITHUB_TOKEN}@github.com/Everloster/bitmagnet.git
git ls-remote origin HEAD

# 配置提交者身份
git config user.email "noreply@bitmagnetagent.ai"
git config user.name "<你的名字> <模型名>"
```

---

## 2. 分支与提交流程

```
main → 主分支，直接提交和推送
```

```bash
# 开发并提交
git add <files>
git commit -m "[feat] scope: 描述

Agent: Claude
Task-Type: feat"

git push origin main
```

### 提交约束钩子

首次 clone 后启用：
```bash
ln -sf ../../scripts/commit-msg .git/hooks/commit-msg
```

提交信息必须包含 `Agent:` 和 `Task-Type:` 字段。

---

## 3. 提交规范

### 格式

```
[{type}] {scope}: {描述}

Agent: {model name}
Task-Type: {type}
```

### Type 分类

| Type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `refactor` | 重构（无功能变化） |
| `perf` | 性能优化 |
| `chore` | 构建/工具变更 |

### 示例

```
[feat] classifier: 添加新的内容类型识别规则

Agent: Claude MiniMax-M2.7
Task-Type: feat
```

---

## 4. 代码审查清单

### 功能性
- [ ] 功能是否符合需求
- [ ] 边界条件是否处理
- [ ] 错误处理是否完善

### 代码质量
- [ ] 命名清晰可读
- [ ] 无重复代码
- [ ] 适当的注释

### 安全
- [ ] 无敏感信息硬编码
- [ ] 输入验证完整
- [ ] SQL/命令注入防护

### 测试
- [ ] 新功能有测试覆盖
- [ ] 边界条件有测试

---

## 5. 安全检查

### 敏感信息扫描

```bash
# 扫描硬编码的敏感信息
grep -rn "password\|secret\|api_key\|token\|private_key\|GITHUB_TOKEN" \
  --include="*.go" --include="*.ts" \
  --exclude-dir=vendor --exclude-dir=node_modules .
```

### Go 依赖安全

```bash
go mod verify
gosec ./...
go vulncheck ./...
```

### 前端依赖安全

```bash
cd webui && npm audit --audit-level=moderate
```

### 数据库迁移检查

```bash
grep -n "DROP\|ALTER\|TRUNCATE" migrations/*.sql
```

---

## 6. 敏感信息处理

- 所有 secrets 必须通过环境变量或 `.env` 注入
- 禁止将 secrets 硬编码到代码或配置文件
- `.env` 不得提交到仓库
- 日志中禁止输出密码、Token、API Key
- 数据库操作使用参数化查询

---

## 7. 本地开发

### 环境要求

- Docker & Docker Compose
- Node.js 18+ (用于 WebUI)

### 快速启动

```bash
docker-compose up -d
```

访问：
- WebUI: http://localhost:3333/webui/
- GraphQL API: http://localhost:3333/graphql

### 常用命令

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 环境变量 (.env)

参考 `.env.example` 创建 `.env`：

```
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=postgres
TMDB_API_KEY=<你的-tmdb-api-key>
```

> 注意：`GITHUB_TOKEN` 等敏感信息不应提交到仓库

---

## 8. 安全铁律

1. **`.env` 绝不可提交**
2. **API Key、密码、密钥等敏感信息禁止提交**
3. **commit message 中不得暴露 token**
4. **依赖更新必须经过安全扫描**
5. **数据目录 `data/` 不得提交**
