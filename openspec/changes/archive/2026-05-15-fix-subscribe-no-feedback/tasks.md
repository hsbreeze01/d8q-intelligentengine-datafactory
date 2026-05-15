# Tasks: 修复策略订阅无反馈

## 1. 全局 API 错误拦截

- [x] **1.1 增强 `api()` 函数的 HTTP status 检查**（`templates/index.html` ~第 315 行）
  - 在 `.then(r => r.json())` 前插入 `r.ok` 判断
  - 非 2xx 时 parse JSON 取 `error` 字段并 throw Error
  - 兜底消息格式：`请求失败 (状态码)`
  - 验证：`ruff check` + `pytest` 通过

## 2. 订阅/取消订阅错误反馈

- [x] **2.1 修复 `subscribeStrategy()` 添加 try/catch 和错误 toast**（`templates/index.html` ~第 469 行）
  - 包裹 `await api(...)` 到 try 块
  - catch 中调用 `toast(e.message, true)` 显示错误
  - 验证：`ruff check` + `pytest` 通过

- [x] **2.2 修复 `unsubscribeStrategy()` 添加 try/catch 和错误 toast**（`templates/index.html` 紧接 subscribeStrategy）
  - 同 2.1 模式
  - 验证：`ruff check` + `pytest` 通过

## 3. 人工验证（scope: frontend）

- [x] **3.1 功能验证**
  - 未登录状态点击"订阅"→ 应显示 toast "请先登录"
  - 已登录状态点击"订阅"→ 应显示 toast "已订阅" 并刷新列表
  - 已登录状态点击"取消订阅"→ 应显示 toast "已取消订阅" 并刷新列表
  - 服务异常时点击"订阅"→ 应显示 toast 包含错误信息
