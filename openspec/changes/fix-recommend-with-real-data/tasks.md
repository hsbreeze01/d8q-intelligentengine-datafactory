# Tasks: 修复推荐页 — 接入真实股票推荐数据

## 1. 后端：Compass 推荐代理路由

- [x] 1.1 添加 COMPASS_API 常量和 compass_request 代理函数
  - 在 `app.py` 中添加 `COMPASS_API = "http://localhost:8087"`
  - 新增 `compass_request(method, path, data=None)` 函数，模式与 `shark_request` 一致
  - 支持 HTTP 错误解析和 502 降级

- [x] 1.2 添加推荐代理路由
  - `GET /api/proxy/recommendation/daily` — 代理到 compass `/api/recommendation/daily`
  - `POST /api/proxy/recommendation/generate` — 代理到 compass `/api/recommendation/generate`，限制 admin 角色
  - 路由注册到 FUNCTION_MAP 用于事件追踪

- [x] 1.3 更新测试
  - 在 `tests/test_recommend_routes.py` 中新增测试：compass 代理路由返回正确状态码、admin 权限校验、502 降级
  - Mock compass_request 以隔离外部依赖

## 2. 前端：推荐页 Tab 化重构 [scope: frontend, 需人工完成]

- [x] 2.1 推荐页三 tab 布局和每日荐股渲染
  - 重构 `loadRecommend` 为三个 tab：每日荐股、行业板块、赛道热度
  - 默认选中"每日荐股"，调用 `/api/proxy/recommendation/daily`
  - 渲染股票评分卡片（代码、名称、综合评分、维度分数、推荐理由、风险提示）
  - 行业板块 tab 调用现有 `/api/search/industries/summary`，空数据时显示"暂无数据"
  - 赛道热度 tab 保留原有逻辑不变
