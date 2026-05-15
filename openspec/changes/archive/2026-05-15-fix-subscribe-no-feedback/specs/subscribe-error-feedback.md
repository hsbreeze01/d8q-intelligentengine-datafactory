# Delta Spec: 策略订阅错误反馈

## ADDED Requirements

### Requirement: API 错误拦截
全局 `api()` 函数 SHALL 在 HTTP 响应状态码非 2xx 时抛出异常，异常消息 MUST 包含服务端返回的 `error` 字段内容；若服务端未返回 `error` 字段，则使用 `请求失败 (状态码)` 作为兜底消息。

#### Scenario: API 返回 4xx/5xx 错误时抛出异常
- Given 前端调用 `api('/api/xxx', opt)`
- When 后端返回 HTTP 401 且 body 为 `{"error": "请先登录"}`
- Then `api()` SHALL 抛出 Error，message 为 `"请先登录"`
- And 调用方的 `catch` 块 SHALL 收到该 Error

#### Scenario: API 返回非 JSON 错误时抛出兜底异常
- Given 前端调用 `api('/api/xxx', opt)`
- When 后端返回 HTTP 502 且 body 非 JSON
- Then `api()` SHALL 抛出 Error，message 为 `"请求失败 (502)"`

---

### Requirement: 订阅操作错误反馈
`subscribeStrategy()` 和 `unsubscribeStrategy()` 函数 MUST 捕获 `api()` 抛出的异常，并通过 toast 向用户展示错误信息。

#### Scenario: 已登录用户订阅成功
- Given 用户已登录
- And 用户在策略发现页点击"订阅"按钮
- When 后端返回 HTTP 200
- Then 页面 SHALL 显示 toast "已订阅"
- And 策略列表 SHALL 刷新

#### Scenario: 未登录用户点击订阅
- Given 用户未登录
- And 用户在策略发现页点击"订阅"按钮
- When 后端返回 HTTP 401 且 body 为 `{"error": "请先登录"}`
- Then 页面 SHALL 显示 toast "请先登录"（错误样式）
- And 不执行列表刷新

#### Scenario: 订阅 API 返回其他错误
- Given 用户点击"订阅"按钮
- When 后端返回 HTTP 500 且 body 为 `{"error": "服务内部错误"}`
- Then 页面 SHALL 显示 toast "服务内部错误"（错误样式）

#### Scenario: 取消订阅成功
- Given 用户已登录且已订阅某策略
- When 用户点击"取消订阅"按钮
- And 后端返回 HTTP 200
- Then 页面 SHALL 显示 toast "已取消订阅"
- And 策略列表 SHALL 刷新

#### Scenario: 取消订阅失败
- Given 用户点击"取消订阅"按钮
- When 后端返回错误
- Then 页面 SHALL 显示 toast 包含错误信息（错误样式）
