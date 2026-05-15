# Specs: fix-subscribe-no-feedback

## spec:api-error-handling

### 概述
增强全局 `api()` 函数，使其在 HTTP 非 2xx 时抛出包含错误信息的异常。

### 修改文件
- `templates/index.html` 第 315 行

### 修改内容
将 `api()` 从 `r.json()` 改为先检查 `r.ok`，非 2xx 时解析 JSON 中的 `error` 字段并抛出 `Error`。

### 验证
- `api('/api/strategy/groups')` 成功时返回数组（不变）
- `api('/api/strategy/subscribe', {method:'POST', ...})` 未登录时抛 `Error("未登录")`

---

## spec:subscribe-error-feedback

### 概述
`subscribeStrategy()` 和 `unsubscribeStrategy()` 增加 try/catch，失败时用 `toast(msg, true)` 显示红色错误提示。

### 修改文件
- `templates/index.html` 第 469-475 行

### 修改内容
两个函数各包裹 try/catch，catch 中调用 `toast(e.message, true)` 显示错误。

### 验证
- 未登录点击订阅 → toast 红色显示"未登录"
- 已登录点击订阅 → toast 绿色显示"已订阅"
