# Delta Spec: Compass 推荐数据代理

## ADDED Requirements

### Requirement: Compass API 代理函数

系统 SHALL 提供 `compass_request(method, path, data=None)` 代理函数，用于将请求转发到 compass 服务（`http://localhost:8087`）。

#### Scenario: 成功代理请求到 compass

- **Given** compass 服务在 `localhost:8087` 正常运行
- **When** 调用 `compass_request("GET", "/api/recommendation/daily")`
- **Then** 返回 compass 的 JSON 响应和 HTTP 200

#### Scenario: compass 服务不可达

- **Given** compass 服务未启动或网络不通
- **When** 调用 `compass_request("GET", "/api/recommendation/daily")`
- **Then** 返回 `{"error": "<异常信息>"}` 和 HTTP 502

---

### Requirement: 每日推荐代理路由

系统 SHALL 提供 `GET /api/proxy/recommendation/daily` 路由，将请求代理到 compass 的 `/api/recommendation/daily`。

#### Scenario: 获取每日推荐列表

- **Given** 用户已登录
- **When** 发送 `GET /api/proxy/recommendation/daily` 请求
- **Then** 返回 compass 的每日股票推荐数据，包含股票代码、名称、综合评分、各维度分数、推荐理由

#### Scenario: compass 返回空数据

- **Given** compass 服务可达但推荐引擎尚未生成当日数据
- **When** 发送 `GET /api/proxy/recommendation/daily` 请求
- **Then** 返回 compass 的原始响应（空列表或提示信息），HTTP 200

#### Scenario: compass 服务异常

- **Given** compass 服务不可达
- **When** 发送 `GET /api/proxy/recommendation/daily` 请求
- **Then** 返回 `{"error": "..."}` 和 HTTP 502

---

### Requirement: 推荐生成触发路由

系统 SHALL 提供 `POST /api/proxy/recommendation/generate` 路由（仅管理员），代理到 compass 的 `/api/recommendation/generate` 以触发推荐计算。

#### Scenario: 管理员触发生成

- **Given** 登录用户角色为 `admin`
- **When** 发送 `POST /api/proxy/recommendation/generate`
- **Then** 请求被代理到 compass，返回生成结果

#### Scenario: 非管理员触发生成

- **Given** 登录用户角色为 `viewer`
- **When** 发送 `POST /api/proxy/recommendation/generate`
- **Then** 返回 `{"error": "仅管理员可操作"}` 和 HTTP 403
