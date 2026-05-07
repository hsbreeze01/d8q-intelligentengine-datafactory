## ADDED Requirements

### Requirement: Monitoring dashboard page
Factory SHALL 提供独立的"运行监控"侧边栏页面（admin 角色），聚合展示基础设施状态和业务监控结果。

#### Scenario: Admin accesses monitoring page
- **WHEN** admin 点击侧边栏"📡 运行监控"
- **THEN** 展示监控页面，包含：顶部告警摘要（异常数量）、基础设施状态面板、业务监控规则面板

#### Scenario: Non-admin cannot see monitoring tab
- **WHEN** viewer/editor 用户查看侧边栏
- **THEN** 侧边栏不显示"运行监控"入口

### Requirement: Infrastructure status panel
监控页面 SHALL 展示所有微服务的实时健康状态，数据来源于现有 `/api/service-status` 端点。

#### Scenario: All services healthy
- **WHEN** 所有 7 个服务正常
- **THEN** 每个服务显示绿色"● 正常"标记，响应时间（ms）

#### Scenario: Service down
- **WHEN** 某服务不可达
- **THEN** 该服务显示红色"● 异常"标记，顶部告警摘要 +1

### Requirement: Business monitor results panel
监控页面 SHALL 展示所有业务监控规则的最新检查结果。

#### Scenario: All monitors passing
- **WHEN** 所有监控规则检查通过
- **THEN** 每条规则显示绿色通过标记

#### Scenario: Monitor rule failing
- **WHEN** 某条规则检查失败
- **THEN** 该规则显示红色失败标记 + 失败原因摘要，告警级别（critical/warning）

### Requirement: Alert summary banner
监控页面顶部 SHALL 显示告警摘要横幅，快速定位异常。

#### Scenario: Has alerts
- **WHEN** 存在异常的服务或监控规则
- **THEN** 顶部红色横幅显示"⚠️ N 项异常"，点击跳转到对应面板

#### Scenario: No alerts
- **WHEN** 所有服务和监控规则正常
- **THEN** 顶部绿色横幅显示"✅ 系统运行正常"

### Requirement: Remove service status from Dashboard
Dashboard 页面 SHALL 不再显示服务状态卡片（移至监控页面）。

#### Scenario: Dashboard no longer shows service status
- **WHEN** admin 访问 Dashboard 页面
- **THEN** 不出现"🖥️ 服务状态"卡片

### Requirement: Auto refresh
监控页面 SHALL 支持自动轮询刷新（默认 30s）和手动刷新按钮。

#### Scenario: Auto refresh
- **WHEN** 监控页面打开
- **THEN** 每 30s 自动刷新监控数据，页面顶部显示上次更新时间
