## ADDED Requirements

### R1: 自动事件采集

**Given** 用户已登录并访问任意页面
**When** 前端发起 `/api/*` 请求
**Then** Factory `after_request` 中间件自动记录事件到 `user_events` 表，包含：user_id、event_time、function_name、method、path、status_code、duration_ms

- 仅记录已登录用户的事件（`session["username"]` 存在时）
- 仅记录 `/api/` 开头的路径（排除静态资源、登录/登出）
- 排除 `/api/auth/` 路径（不记录登录/登出行为）
- 排除 `/api/analytics/` 路径（避免自循环）

### R2: 功能归类

**Given** 一个 API 路径
**When** 事件被记录
**Then** 根据路径前缀匹配 FUNCTION_MAP 归类为功能名称

- 路径按 FUNCTION_MAP 键的长度降序匹配（最精确优先）
- 未匹配的路径归类为"其他"

### R3: 事件存储

**Given** 系统启动
**When** `user_events` 表不存在
**Then** 自动创建表及索引（CREATE TABLE IF NOT EXISTS）

- SQLite 使用 WAL 模式
- `user_events` 表存储在 Agent 的 `financial_news.db` 中

### R4: 数据自动清理

**Given** 系统运行中
**When** 每天首次有 API 请求
**Then** 检查并删除 90 天前的原始事件记录

- 清理操作每天最多执行一次
- 不影响聚合数据

### R5: 性能约束

- 事件写入耗时 < 5ms（P99）
- 不阻塞 API 响应返回
- 写入失败时静默降级（不影响正常 API 功能）
