## ADDED Requirements

### Requirement: Start cookie capture session
Infopublisher SHALL provide `POST /api/cookie/capture` 端点，接收 `platform` 参数（默认 `xiaohongshu`），启动异步浏览器登录捕获任务。该端点 SHALL 在后台线程中打开浏览器导航到平台登录页，并返回 `{task_id, status: "waiting_login"}`。

#### Scenario: Successfully start capture
- **WHEN** admin 发送 `POST /api/cookie/capture` 且无正在进行的 capture 任务
- **THEN** 返回 `{task_id: "<uuid>", status: "waiting_login", login_url: "https://creator.xiaohongshu.com/login"}`，后台线程启动浏览器

#### Scenario: Capture already in progress
- **WHEN** admin 发送 `POST /api/cookie/capture` 但已有 capture 任务正在执行
- **THEN** 返回 `{error: "正在更新中，请稍候", status: "in_progress"}`，HTTP 409

#### Scenario: Publish task conflict
- **WHEN** admin 发送 `POST /api/cookie/capture` 但浏览器正在执行发布任务
- **THEN** 返回 `{error: "浏览器正在执行发布任务，请稍后重试"}`，HTTP 409

### Requirement: Query capture progress
Infopublisher SHALL 提供 `GET /api/cookie/capture-status` 端点，返回当前 capture 任务进度。

#### Scenario: Capture in progress — waiting for login
- **WHEN** 查询进度且用户尚未完成登录
- **THEN** 返回 `{status: "waiting_login", elapsed_sec: <秒数>, message: "请在手机小红书 App 扫码登录"}`

#### Scenario: Capture completed successfully
- **WHEN** 查询进度且检测到登录成功，Cookie 已保存
- **THEN** 返回 `{status: "completed", cookie_count: <数量>, message: "Cookie 更新成功"}`

#### Scenario: Capture timed out
- **WHEN** 查询进度且等待超过 120 秒
- **THEN** 返回 `{status: "timeout", message: "等待登录超时，请重新操作"}`

#### Scenario: Capture failed
- **WHEN** 查询进度且浏览器异常或 Cookie 捕获失败
- **THEN** 返回 `{status: "failed", message: "<错误信息>"}`

#### Scenario: No active capture
- **WHEN** 查询进度但没有正在进行的 capture 任务
- **THEN** 返回 `{status: "idle", message: "无进行中的更新"}`

### Requirement: Auto-detect login success
系统 SHALL 通过检测浏览器 URL 变化判断登录成功：当 URL 从 login 页面跳转到 `creator.xiaohongshu.com/publish` 或不再包含 `login` 时，判定登录成功。

#### Scenario: URL redirected to publish page
- **WHEN** 浏览器 URL 变为包含 `creator.xiaohongshu.com/publish`
- **THEN** 判定登录成功，延迟 2 秒后捕获 Cookie

### Requirement: Save captured cookies
登录成功后，系统 SHALL 调用 `_save_cookies_from_browser(page)` 保存 Cookie，并通过 `CookieManager.save()` 持久化到文件。

#### Scenario: Cookies saved successfully
- **WHEN** 登录成功且 Cookie 已保存
- **THEN** Cookie 文件更新，capture status 变为 `completed`

### Requirement: Cleanup on completion
无论 capture 成功、失败或超时，系统 SHALL 释放浏览器资源（release page）、清理临时锁文件、重置 `_capture_in_progress` 标志。

#### Scenario: Cleanup after success
- **WHEN** Cookie 捕获完成
- **THEN** 浏览器 release、`_capture_in_progress=False`、发布锁清理

#### Scenario: Cleanup after timeout
- **WHEN** 等待超过 120 秒
- **THEN** 浏览器 release、`_capture_in_progress=False`、发布锁清理
