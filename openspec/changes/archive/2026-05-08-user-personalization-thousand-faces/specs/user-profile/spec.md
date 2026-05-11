## ADDED Requirements

### Requirement: User subscription CRUD API
Agent 服务 SHALL 提供 `/api/user/subscribe` 系列端点，支持用户订阅/取消赛道、查询已订阅赛道列表。

#### Scenario: Subscribe to a track
- **WHEN** POST `/api/user/subscribe` with body `{user_id: "lancer", track_id: 1}`
- **THEN** 在 `user_subscriptions` 表插入记录，返回 `{success: true}`

#### Scenario: Unsubscribe from a track
- **WHEN** DELETE `/api/user/subscribe/{user_id}/{track_id}`
- **THEN** 删除 `user_subscriptions` 对应记录，返回 `{success: true}`

#### Scenario: List user subscriptions
- **WHEN** GET `/api/user/{user_id}/subscriptions`
- **THEN** 返回该用户订阅的所有赛道列表 `[{track_id, track_name, ...}]`

### Requirement: User preferences KV store
Agent 服务 SHALL 提供 `/api/user/preferences` 端点，支持用户偏好的读写。

#### Scenario: Save a preference
- **WHEN** PUT `/api/user/preferences` with body `{user_id: "lancer", key: "default_days", value: "7"}`
- **THEN** 在 `user_preferences` 表 upsert 记录，返回 `{success: true}`

#### Scenario: Get user preferences
- **WHEN** GET `/api/user/{user_id}/preferences`
- **THEN** 返回该用户所有偏好键值对 `{default_days: "7", sort_order: "latest"}`

### Requirement: Watchlist API integration
Agent 服务 SHALL 将现有 `user_watchlist` 表暴露为标准 API，Factory 不再本地管理 watchlist。

#### Scenario: Get user watchlist
- **WHEN** GET `/api/user/{user_id}/watchlist`
- **THEN** 返回该用户所有自选股 `[{stock_code, stock_name}]`

#### Scenario: Add to watchlist
- **WHEN** POST `/api/user/watchlist` with body `{user_id: "lancer", stock_code: "002594", stock_name: "比亚迪"}`
- **THEN** 在 `user_watchlist` 表插入记录

#### Scenario: Remove from watchlist
- **WHEN** DELETE `/api/user/{user_id}/watchlist/{stock_code}`
- **THEN** 删除 `user_watchlist` 对应记录

### Requirement: User database schema migration
Agent 服务 SHALL 在启动时自动创建 `user_preferences` 表（如不存在），确保 `user_subscriptions` 和 `user_watchlist` 表存在且结构正确。

#### Scenario: First startup with new schema
- **WHEN** Agent 服务启动
- **THEN** `user_preferences(user_id TEXT, key TEXT, value TEXT, created_at DATETIME, PRIMARY KEY(user_id, key))` 表被创建
