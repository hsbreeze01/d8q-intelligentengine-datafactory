## Context

D8Q 智能资讯平台当前有 9 个用户账号（1 admin + 2 editor + 6 viewer），所有用户看到完全相同的数据：5 个赛道、全部资讯流、无差别的股票和研报。

现有基础设施：
- **认证**：Flask session 认证，`session["username"]` 作为用户标识，角色分为 viewer/editor/admin
- **数据库**：Agent SQLite 已有 `user_subscriptions(user_id, track_id)` 和 `user_watchlist(user_id, stock_code, stock_name)` 表，但均为空（watchlist 仅 3 条测试数据）
- **前端**：SPA 架构（index.html），所有数据通过 Factory `/api/*` 端点获取，Factory 作为聚合层代理 Agent/Shark/Compass

关键约束：
- 无新增基础设施（无新服务、无新中间件）
- 服务间调用（localhost 内部请求）不受用户过滤影响
- admin 需保留全局视图能力

## Goals / Non-Goals

**Goals:**
- 每位用户登录后只看到自己关注的赛道内容和自选股
- Dashboard/Feed/Policy/Report/Stock 各页面数据默认按用户订阅过滤
- 提供赛道订阅管理界面和自选股管理界面
- admin 可切换"个人视图"和"全局视图"
- 改造渐进式：无用户订阅时显示全部（向后兼容）

**Non-Goals:**
- 不做个性化推荐算法（本期仅基于显式订阅）
- 不做用户间社交/分享功能
- 不改 Agent/Shark/Compass 底层数据结构
- 不做多租户数据物理隔离（仅逻辑过滤）

## Decisions

### D1: 用户数据存储位置 — Agent SQLite

**选择**：用户订阅/偏好数据存在 Agent 的 `financial_news.db`，Factory 通过 Agent API 读写。

**理由**：
- `user_subscriptions`、`user_watchlist` 表已在 Agent 库中
- Agent 是数据中枢，拥有 tracks/news 全部数据，过滤逻辑在数据源头最高效
- Factory 只需透传 `user_id` 参数

**替代方案**：Factory 本地存储（JSON 文件）——rejected，无法与 Agent 数据关联查询。

### D2: 过滤执行层 — Factory API 层

**选择**：Factory API 端点接收 `username`（从 session 读取），传给 Agent API 作为过滤参数。Agent 返回已过滤数据。

**理由**：
- Factory 是用户请求入口，天然持有 session 信息
- Agent 不接触用户 session，通过参数接收 user_id
- 单一过滤点，避免各服务各自实现过滤逻辑

### D3: 前端策略 — 默认过滤 + 手动切全局

**选择**：
1. 前端每个页面加载时从 session 获取 username，传给 API
2. 默认只展示用户订阅的内容
3. admin 角色在页面顶部显示"全局视图 / 我的视图"切换按钮
4. 无订阅的新用户看到全部内容（引导订阅）

**理由**：渐进式上线，不破坏现有用户体验。

### D4: 数据模型 — 复用现有表 + 补充偏好表

**选择**：
- `user_subscriptions(user_id, track_id)` — 已有，直接用
- `user_watchlist(user_id, stock_code, stock_name)` — 已有，直接用
- 新增 `user_preferences(user_id, key, value)` — 通用偏好 KV 存储（如默认时间范围、排序方式等）

### D5: API 设计 — 参数化过滤

**选择**：现有 API 端点新增可选参数 `user_id`，有值时按订阅过滤，无值时返回全部。

示例：`/api/news?user_id=lancer` 只返回 lancer 订阅赛道的资讯。

**理由**：向后兼容，内部服务间调用不传 user_id 即获取全量。

## Risks / Trade-offs

- **[空订阅用户]** → 新用户首次登录无订阅，默认显示全部内容 + 引导订阅提示条
- **[订阅变更延迟]** → 用户订阅/取消赛道后，已加载的页面数据需手动刷新。不引入 WebSocket 推送
- **[admin 全局视图]** → 通过额外参数 `view=all` 实现，不破坏 session 逻辑
- **[性能]** → 过滤在 SQL 层完成（WHERE track_id IN (...)），对 Agent 查询性能影响极小
