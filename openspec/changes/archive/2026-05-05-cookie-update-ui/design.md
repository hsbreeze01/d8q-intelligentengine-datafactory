## Context

当前 D8Q 平台通过 Infopublisher 服务（Flask + patchright 浏览器池）发布内容到小红书等平台。Cookie 存储在 `data/cookies/{platform}_cookies.json`，由 `CookieManager` 管理。目前更新 Cookie 的唯一方式是在服务器上运行 `capture_cookies_interactive()` 命令行脚本，需要 SSH 访问权限。

已有基础设施：
- `BrowserPool`：基于 CDP 连接 Ghost Browser（patchright 反检测），acquire/release 单实例模式
- `CookieManager.check_expiry(platform)`：返回 `{valid, expired_fields, warn_fields, message}`
- `CookieManager.save(platform, cookies)`：保存 cookie 列表到 JSON 文件
- `_save_cookies_from_browser(page)`：从浏览器 page.context 提取 cookies 并保存
- Cookie 验证端点 `/api/cookie/validate`（耗时 ~15s，需要打开浏览器导航）
- Cookie 状态端点 `/api/cookie/status`（纯本地文件检查，毫秒级）

Factory 是前端 SPA（`templates/index.html`），所有 API 调用通过 `api()` helper。已有监控页面展示 Cookie 规则状态。

## Goals / Non-Goals

**Goals:**
- 用户在 Factory 前端点击「更新 Cookie」→ 后端启动浏览器打开登录页 → 用户扫码登录 → 自动捕获并保存 Cookie
- 引导流程极简：3 步完成（点击 → 扫码 → 完成）
- 复用现有 BrowserPool 和 CookieManager
- 在监控页面 Cookie 规则处展示状态和操作入口

**Non-Goals:**
- 不做支持多平台扩展（当前只做小红书，架构预留即可）
- 不做 Cookie 历史记录/版本管理
- 不做自动定时更新（仅手动触发）
- 不做 VNC/远程桌面方式让用户看到浏览器（服务器无桌面环境）

## Decisions

### D1: 使用"无头浏览器 + URL 检测"而非 VNC 远程桌面

**选择**: 后端启动浏览器打开登录页，通过检测 URL 变化判断登录成功，自动捕获 Cookie。前端通过轮询后端获取进度。

**理由**: 服务器无桌面环境，无法提供 VNC。patchright 无头模式足以完成扫码登录（小红书登录页是手机扫码，不需要看到浏览器界面）。

**替代方案**:
- VNC/noVNC → 需要安装桌面环境，复杂度高
- 用户粘贴 Cookie JSON → 技术门槛高，容易出错

### D2: 长轮询进度 API 而非 WebSocket

**选择**: `POST /api/cookie/capture` 启动异步任务，`GET /api/cookie/capture-status` 轮询进度（2s 间隔），前端显示步骤进度。

**理由**: Factory 是单 worker gunicorn，WebSocket 需要额外依赖。轮询简单可靠，2s 间隔用户无感知。

### D3: BrowserPool 增加重入保护

**选择**: capture 任务执行期间设置 `_capture_in_progress` 标志，拒绝并发 capture 请求。

**理由**: BrowserPool 是单实例，capture 需要独占浏览器。发布任务和 capture 不能同时进行。

### D4: Factory 代理 Infopublisher API

**选择**: Factory 后端新增 `/api/cookie/capture` 和 `/api/cookie/capture-status` 代理到 Infopublisher 的同路径端点。前端统一走 Factory 域名。

**理由**: 前端只访问 Factory（8088 端口），避免跨域。与现有 `/api/cookie/validate` 代理模式一致。

## Risks / Trade-offs

- **[用户看不到浏览器界面]** → 前端用文字步骤引导："正在打开登录页...请在手机小红书 App 扫码登录"，显示等待时间和步骤状态
- **[扫码超时]** → 设置 120s 超时，前端倒计时展示，超时后自动清理浏览器状态
- **[capture 与发布冲突]** → `_capture_in_progress` 标志 + 发布前检查，冲突时返回友好提示
- **[patchright 浏览器崩溃]** → BrowserPool 已有 `_reconnect()` 机制，capture 失败时清理标志
- **[Cookie 文件写入冲突]** → capture 保存和 validate 读取使用同一文件，但 validate 在 capture 完成后才会获取到新数据，无写冲突
