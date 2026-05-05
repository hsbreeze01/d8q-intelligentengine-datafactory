## 1. Infopublisher — Cookie 捕获 API

- [x] 1.1 新增全局 `_capture_state` 字典，存储 capture 任务状态（task_id, status, message, elapsed_sec, cookie_count, started_at）
- [x] 1.2 新增 `_run_capture(platform)` 后台线程函数：acquire 浏览器 → 导航到登录页 → 循环检测 URL 变化（120s 超时）→ 成功时 save cookies → 更新 `_capture_state` → finally 释放资源
- [x] 1.3 新增 `POST /api/cookie/capture` 端点：检查 `_capture_in_progress` 标志，无冲突则启动线程并返回 `{task_id, status: "waiting_login"}`
- [x] 1.4 新增 `GET /api/cookie/capture-status` 端点：返回 `_capture_state` 当前值（idle/waiting_login/completed/timeout/failed）
- [x] 1.5 验证：curl 测试 capture 启动 → 轮询 status → 确认超时/完成状态正确

## 2. Factory — API 代理

- [x] 2.1 新增 `POST /api/cookie/capture` 代理端点（admin-only），转发到 Infopublisher
- [x] 2.2 新增 `GET /api/cookie/capture-status` 代理端点（admin-only），转发到 Infopublisher
- [x] 2.3 验证：通过 Factory 域名 curl 测试代理功能正常

## 3. Factory 前端 — Cookie 更新 UI

- [x] 3.1 监控页面 Cookie 规则增加「更新 Cookie」按钮（error 时红色高亮，ok 时灰色）
- [x] 3.2 新增 `updateCookie()` 函数：弹出引导弹窗，调用 capture API，启动轮询
- [x] 3.3 弹窗分步展示：步骤1"正在打开登录页" → 步骤2"请扫码登录（已等待 Ns）" → 步骤3 成功/失败
- [x] 3.4 成功后自动关闭弹窗并刷新监控页面（loadMonitor）
- [x] 3.5 超时/失败时显示错误信息和「重试」/「关闭」按钮
- [x] 3.6 验证：浏览器测试完整流程

## 4. 验收测试

- [x] 4.1 Admin 在监控页面看到 Cookie 规则和「更新 Cookie」按钮
- [x] 4.2 点击更新 → 弹窗显示引导 → 轮询进度正常
- [x] 4.3 Viewer 无法访问 capture API（403）
- [x] 4.4 发布任务进行中时 capture 返回冲突提示
- [x] 4.5 Cookie 更新成功后监控页面自动刷新显示新状态
