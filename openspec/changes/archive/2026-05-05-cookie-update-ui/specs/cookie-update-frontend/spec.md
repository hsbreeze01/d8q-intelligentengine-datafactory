## ADDED Requirements

### Requirement: Cookie update button in monitor page
监控页面 Cookie 规则卡片 SHALL 显示「更新 Cookie」按钮，当 Cookie 状态为 error 或 warning 时高亮显示。

#### Scenario: Cookie invalid — show update button
- **WHEN** Cookie 规则状态为 error（Cookie 已过期或无效）
- **THEN** 规则卡片右侧显示红色「更新 Cookie」按钮

#### Scenario: Cookie valid — show update button dimmed
- **WHEN** Cookie 规则状态为 ok（Cookie 有效）
- **THEN** 规则卡片右侧显示灰色「更新」按钮，可点击但不高亮

### Requirement: Cookie update guided modal
点击「更新 Cookie」后 SHALL 弹出引导弹窗，分步骤展示更新流程：步骤1 打开登录页 → 步骤2 等待扫码 → 步骤3 完成。

#### Scenario: Modal opens and starts capture
- **WHEN** 用户点击「更新 Cookie」
- **THEN** 弹窗显示，自动调用 capture API，显示"正在打开登录页..."

#### Scenario: Progress polling
- **WHEN** capture 已启动
- **THEN** 每 2 秒轮询 capture-status，弹窗显示当前步骤和已等待时间（秒数）

#### Scenario: Login completed
- **WHEN** capture-status 返回 `completed`
- **THEN** 弹窗显示 ✅ "Cookie 更新成功！已捕获 N 个 Cookie"，显示「完成」按钮

#### Scenario: Login timeout
- **WHEN** capture-status 返回 `timeout`
- **THEN** 弹窗显示 ❌ "等待超时，请重新操作"，显示「重试」和「关闭」按钮

#### Scenario: Capture failed
- **WHEN** capture-status 返回 `failed`
- **THEN** 弹窗显示 ❌ 错误信息，显示「关闭」按钮

### Requirement: Refresh monitor after cookie update
Cookie 更新成功后，SHALL 自动刷新监控页面数据（重新调用 loadMonitor），展示新的 Cookie 状态。

#### Scenario: Auto refresh after success
- **WHEN** 用户在成功弹窗中点击「完成」
- **THEN** 关闭弹窗，监控页面自动刷新，Cookie 规则状态更新为 ok

### Requirement: Factory proxy for cookie capture APIs
Factory 后端 SHALL 代理 Infopublisher 的 capture 相关 API，前端统一通过 Factory 域名访问。

#### Scenario: Proxy capture request
- **WHEN** 前端发送 `POST /api/cookie/capture` 到 Factory（8088）
- **THEN** Factory 转发请求到 Infopublisher（8089），返回结果

#### Scenario: Proxy capture-status request
- **WHEN** 前端发送 `GET /api/cookie/capture-status` 到 Factory（8088）
- **THEN** Factory 转发请求到 Infopublisher（8089），返回结果

#### Scenario: Admin-only access
- **WHEN** 非 admin 用户访问 capture API
- **THEN** 返回 403 权限不足
