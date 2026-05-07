## ADDED Requirements

### Requirement: Monitor rules CRUD API
Factory SHALL 提供 `/api/monitor/rules` 端点，支持监控规则的增删改查。

#### Scenario: List all rules
- **WHEN** GET `/api/monitor/rules`
- **THEN** 返回所有监控规则列表 `[{id, name, type, config, severity, enabled, interval_sec, last_check}]`

#### Scenario: Create custom rule
- **WHEN** POST `/api/monitor/rules` with body `{name: "StockShark 延迟", type: "http", config: {url: "http://localhost:5000/health", timeout: 3}, severity: "warning", interval_sec: 60}`
- **THEN** 创建规则并返回 `{id, success: true}`

#### Scenario: Update rule
- **WHEN** PUT `/api/monitor/rules/<id>` with body `{enabled: false}`
- **THEN** 更新规则配置

#### Scenario: Delete custom rule
- **WHEN** DELETE `/api/monitor/rules/<id>`
- **THEN** 删除规则（内置规则不可删除，返回 403）

### Requirement: Monitor status API
Factory SHALL 提供 `/api/monitor/status` 端点，返回所有规则和服务的实时检查结果。

#### Scenario: Get current status
- **WHEN** GET `/api/monitor/status`
- **THEN** 返回 `{services: {...}, rules: [{rule_id, name, status, message, checked_at}], alert_count: N, timestamp: "..."}`

#### Scenario: Cached results
- **WHEN** 规则的上次检查时间距今 < interval_sec
- **THEN** 返回缓存的检查结果，不重新执行检查

### Requirement: Built-in publish monitor rules
系统 SHALL 内置 4 个不可删除的发布监控规则。

#### Scenario: Cookie validity check
- **WHEN** 系统检查"小红书 Cookie 有效性"规则
- **THEN** 调用 `http://localhost:8089/api/cookie/validate`，valid=true 时通过，severity=critical

#### Scenario: Ghost Browser CDP check
- **WHEN** 系统检查"Ghost Browser CDP 连通性"规则
- **THEN** 调用 `http://localhost:9222/json/version`，返回 200 时通过，severity=critical

#### Scenario: Publish lock check
- **WHEN** 系统检查"发布锁状态"规则
- **THEN** 检查 `/tmp/d8q_publishing.lock` 文件，不存在时通过，存在超过 10 分钟时 warning，severity=warning

#### Scenario: Infopublisher health check
- **WHEN** 系统检查"发布服务健康"规则
- **THEN** 调用 `http://localhost:8089/api/health`，返回 `{status: "ok"}` 时通过，severity=critical

### Requirement: Rule types
监控规则 SHALL 支持 3 种检查类型：`http`、`system`、`custom`。

#### Scenario: HTTP rule
- **WHEN** 规则 type 为 `http`
- **THEN** 对 config.url 发送 GET 请求，config.timeout 内返回 2xx 状态码即为通过

#### Scenario: System rule
- **WHEN** 规则 type 为 `system`
- **THEN** 执行 config.check（systemd_status / file_exists / port_open），返回布尔结果

#### Scenario: Custom rule
- **WHEN** 规则 type 为 `custom`
- **THEN** 调用 config.url，解析 JSON 响应，用 config.judge 表达式判断状态

### Requirement: Monitor rules database
Factory SHALL 在启动时自动创建 `monitor_rules` 和 `monitor_results` 表。

#### Scenario: First startup
- **WHEN** Factory 服务启动
- **THEN** 创建 `monitor_rules(id INTEGER PRIMARY KEY, name TEXT, type TEXT, config_json TEXT, severity TEXT, enabled INTEGER, builtin INTEGER, interval_sec INTEGER, created_at DATETIME)` 表
- **AND** 创建 `monitor_results(rule_id INTEGER, status TEXT, message TEXT, detail_json TEXT, checked_at DATETIME)` 表
- **AND** 插入 4 条内置发布监控规则（builtin=1）
