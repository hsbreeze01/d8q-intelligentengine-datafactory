## Why

D8Q 平台即将面向多个终端用户（当前已有 9 个账号）。所有用户看到完全相同的赛道、资讯、股票数据——投 AI 的人和看碳纤维的人混在一起，体验混乱且低效。需要实现**千人千面**：每位用户只看到自己关注的赛道和自选股，首页 Dashboard、资讯 Feed、政策分析、研报等内容全部基于用户订阅过滤，同时支持管理员统揽全局。

## What Changes

- **用户配置模型**：扩展用户数据结构，支持"关注的赛道"和"自选股"作为用户个性化核心维度
- **数据过滤层**：所有面向用户的数据 API 加入 `user_id` 维度过滤——资讯按用户订阅赛道筛选、个股按自选股筛选、政策/研报按关联赛道筛选
- **首页个性化**：Dashboard 从"全局概览"变为"我的概览"——只展示用户关注赛道的指标、要闻、热度趋势
- **全页面联动**：资讯 Feed 默认只推订阅赛道的资讯、政策分析默认只分析订阅赛道的政策、研报默认只展示订阅赛道的研报
- **管理员视图**：admin 角色可切换"个人视图"和"全局视图"，统揽所有赛道
- **数据存储**：利用已有的 `user_subscriptions`、`user_watchlist`、`user_bookmarks` 表，补充用户偏好配置表
- **前端交互**：新增"我的关注"管理入口，支持订阅/取消赛道、管理自选股

## Capabilities

### New Capabilities
- `user-profile`: 用户个性化配置管理——用户订阅赛道、自选股、内容偏好设置的 CRUD API 和存储
- `personalized-feed`: 基于用户订阅的数据过滤层——所有数据 API 按用户关注维度过滤，实现千人千面内容展示
- `personalized-dashboard`: 个性化首页——按用户订阅赛道的定制化 Dashboard，包含订阅赛道指标、推荐要闻、自选股动态

### Modified Capabilities
<!-- 无现有 openspec specs，首次引入 -->

## Impact

- **后端 API**：Factory 的 `/api/news`、`/api/proxy/tracks`、`/api/stock/*`、`/api/policy/*`、`/api/report/*` 等端点需要支持 `user_id` 过滤参数
- **前端 SPA**：`loadDashboard`、`loadFeed`、`loadStock`、`loadPolicy`、`loadReport` 全部接入用户过滤参数；新增"我的关注"管理页面
- **数据层**：Agent 数据库的 `user_subscriptions` 表已有但为空，需要 API 接入；新增 `user_preferences` 表存储通用偏好
- **认证**：现有 session 认证已存储 `username`，以此作为 `user_id`，无需新增认证机制
- **兼容性**：admin 角色保留全局视图能力；内部 IP 调用（服务间通信）不受用户过滤影响
