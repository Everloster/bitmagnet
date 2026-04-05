# Bitmagnet — AI 协作规范 v1.1

> 本项目 fork 自 [bitmagnet-io/bitmagnet](https://github.com/bitmagnet-io/bitmagnet)，遵守 MIT 协议。

---

## §0 Git 初始化

```bash
GITHUB_TOKEN=$(grep GITHUB_TOKEN .env | cut -d'"' -f2)
git remote set-url origin https://${GITHUB_TOKEN}@github.com/Everloster/bitmagnet.git
git ls-remote origin HEAD          # 验权，失败则停止
git config user.email "noreply@everagent.ai"
```

---

## §1 分支策略

```
main                    → 稳定发布分支（保护分支），仅通过 PR 合并
feature/{描述}          → 新功能分支
fix/{描述}              → Bug 修复分支
refactor/{描述}         → 重构分支
docs/{描述}             → 文档更新分支
```

**规则**：
- 分支命名使用小写字母和连字符
- 所有分支从 `main` 创建
- 合并前必须通过 CI 检查
- 禁止直接在 `main` 分支操作

---

## §2 Commit Message 格式

```
[{type}] {scope}: {描述}

Agent: {model name}
Task-Type: {feat | fix | docs | refactor | perf | chore}
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

### 完整示例

```
[feat] classifier: 添加新的内容类型识别规则

Agent: Claude
Task-Type: feat

BREAKING CHANGE: 分类器返回值结构变更
Closes: #123
```

---

## §3 推送流程

```bash
# 1. 确保在功能分支
git checkout -b feature/my-feature

# 2. 开发并提交
git add -A
git commit -m "[feat] scope: 添加新功能

Agent: Claude
Task-Type: feat"

# 3. 获取最新 main
git fetch origin main
git rebase origin/main

# 4. 推送并创建 PR
git push -u origin feature/my-feature
```

---

## §4 代码贡献流程

```
1. 从 main 创建功能分支
2. 开发 & 编写测试
3. 运行安全检查清单（见 §6）
4. 提交并推送
5. 创建 Pull Request
6. Code Review 通过后合并
7. 删除已合并分支
```

### Pull Request 要求

- 标题清晰描述变更内容
- 包含变更说明和测试结果
- 所有 CI 检查必须通过
- 至少一个 Reviewer 批准

---

## §5 Code Review 要点

审查代码时重点关注：

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
- [ ] 测试可重复执行

---

## §6 安全检查清单

**提交前必须通过以下所有检查**：

### 敏感信息扫描

```bash
# 扫描硬编码的敏感信息（Go）
grep -rn "password\|secret\|api_key\|token\|private_key\|GITHUB_TOKEN" \
  --include="*.go" --include="*.ts" --include="*.js" \
  --exclude-dir=vendor --exclude-dir=node_modules .

# 扫描可疑的日志输出
grep -rn "fmt\.Print\|log\.\|console\." \
  --include="*.go" --include="*.ts" internal/
```

### Go 依赖安全

```bash
# 验证依赖完整性
go mod verify

# 安全扫描（如有 gosec）
gosec ./...

# 检查是否有已知漏洞
go vulncheck ./...
```

### 前端依赖安全（WebUI）

```bash
cd webui
npm audit --audit-level=moderate
```

### 数据库迁移检查

```bash
# 确保迁移文件语法正确
# 检查是否有破坏性变更
grep -n "DROP\|ALTER\|TRUNCATE" migrations/*.sql
```

---

## §7 敏感信息处理规范

### 环境变量

- 所有运行时 secrets 必须通过环境变量注入
- 禁止将 secrets 硬编码或写入配置文件
- 提供 `.env.example` 模板（仅包含变量名，无实际值）

### 日志规范

- 禁止在日志中输出用户密码、Token、API Key
- 敏感数据字段用 `***` 脱敏
- 请求/响应日志需配置脱敏规则

### 内存安全

- 密码等敏感数据使用后及时清零
- 避免在日志或错误信息中暴露敏感内容
- 使用 `crypto/subtle` 处理敏感比较

### 数据库

- 密码字段必须加密存储
- 禁止在 SQL 中拼接用户输入（使用参数化查询）
- 敏感操作需记录审计日志

---

## §8 安全铁律

1. **Token 安全**：`.env` 绝不可提交；commit message 中不得暴露 token
2. **敏感信息**：API Key、密码、密钥等禁止提交
3. **数据目录**：`data/` 目录已加入 .gitignore，不得提交
4. **二进制文件**：`bitmagnet` 二进制文件已加入 .gitignore，不得提交
5. **依赖安全**：依赖更新必须经过安全扫描
6. **CI 必须**：所有 PR 必须通过自动化安全检查
