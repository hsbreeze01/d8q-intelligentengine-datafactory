## Why

发布平台（小红书等）的 Cookie 会定期过期失效，导致发布失败。当前更新 Cookie 需要手动登录服务器操作，非技术人员无法独立完成。需要一个前端界面让用户自助完成 Cookie 更新，引导用户在弹出的浏览器中扫码登录，自动捕获并保存 Cookie。

## What Changes

- 新增 Infopublisher API 端点：`POST /api/cookie/capture` 启动浏览器引导用户登录并捕获 Cookie
- 新增 `GET /api/cookie/capture-status` 查询捕获进度（等待登录 → 检测中 → 完成/失败）
- Factory 监控页面的 Cookie 规则旁增加「更新 Cookie」操作按钮
- 前端弹窗引导流程：展示当前状态 → 点击更新 → 显示进度 → 完成/失败反馈
- Cookie 状态信息增强：显示关键 Cookie 数量、过期/即将过期数量

## Capabilities

### New Capabilities
- `cookie-capture-api`: Infopublisher 新增的 Cookie 捕获 API（启动浏览器、捕获进度、保存结果）
- `cookie-update-frontend`: Factory 前端 Cookie 更新 UI（引导弹窗、进度反馈、状态展示）

### Modified Capabilities
（无现有 spec 需要修改）

## Impact

- **Infopublisher server.py**: 新增 2 个 API 端点，复用现有 BrowserPool
- **Factory index.html**: 监控页面 Cookie 规则增加操作按钮 + 更新弹窗
- **Factory app.py**: 代理 Infopublisher 的 Cookie 捕获 API（前端统一走 Factory 域名）
- **依赖**: BrowserPool 的 acquire/release 机制需适配"长占用"场景（用户扫码可能需要 1-2 分钟）
