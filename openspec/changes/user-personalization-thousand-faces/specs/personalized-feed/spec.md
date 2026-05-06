## ADDED Requirements

### Requirement: News API supports user-scoped filtering
Factory 的 `/api/news` 端点 SHALL 接受 `user_id` 参数，当提供时只返回该用户订阅赛道的资讯。

#### Scenario: User with subscriptions sees filtered news
- **WHEN** GET `/api/news?user_id=lancer` and lancer subscribed to tracks [1, 3]
- **THEN** 返回 subject IN ("人工智能", "新材料") 的资讯，其他赛道资讯不返回

#### Scenario: User without subscriptions sees all news
- **WHEN** GET `/api/news?user_id=newuser` and newuser has no subscriptions
- **THEN** 返回全部资讯（等同于不带 user_id 的请求）

#### Scenario: Admin with global view sees all news
- **WHEN** GET `/api/news?user_id=admin&view=all`
- **THEN** 返回全部资讯，忽略用户订阅

### Requirement: Track API supports user-scoped filtering
Factory 的 `/api/proxy/tracks` 端点 SHALL 接受 `user_id` 参数，只返回用户订阅的赛道。

#### Scenario: User sees only subscribed tracks
- **WHEN** GET `/api/proxy/tracks?user_id=lancer` and lancer subscribed to tracks [1, 5]
- **THEN** 只返回"人工智能"和"碳纤维"两个赛道的元数据

#### Scenario: Track heat data filtered by user
- **WHEN** GET `/api/proxy/tracks/heat?user_id=lancer`
- **THEN** 只返回用户订阅赛道的热度数据

### Requirement: Report API supports user-scoped filtering
Factory 的研报 API SHALL 接受 `user_id` 参数，默认只展示用户订阅赛道的研报。

#### Scenario: User sees only subscribed track reports
- **WHEN** GET `/api/research/track/{track_id}` with user_id=lancer and lancer not subscribed to track_id=4
- **THEN** 返回 403 或空数据（不允许查看未订阅赛道的研报）

#### Scenario: Admin sees all track reports
- **WHEN** admin 请求任意 track_id 的研报
- **THEN** 正常返回研报数据

### Requirement: Policy analysis scoped to user tracks
Factory 的政策分析功能 SHALL 默认只分析用户订阅赛道的资讯。

#### Scenario: Batch classify for user tracks
- **WHEN** 用户点击"批量AI识别"且 user_id=lancer
- **THEN** 只对 lancer 订阅赛道的资讯进行政策识别

### Requirement: Internal service calls bypass user filtering
服务间内部调用（127.0.0.1）SHALL 不受 user_id 过滤影响。

#### Scenario: Compass calls Agent for data
- **WHEN** Compass 从 127.0.0.1 调用 Agent API
- **THEN** 返回全量数据，不进行用户过滤
