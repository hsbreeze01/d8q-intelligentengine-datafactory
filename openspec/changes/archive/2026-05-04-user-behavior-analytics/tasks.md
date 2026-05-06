## 1. 事件存储与采集层

- [x] 1.1 Agent `user_routes.py` 新增 `user_events` 表创建（CREATE TABLE IF NOT EXISTS + 索引），设置 SQLite WAL 模式
- [x] 1.2 Factory `app.py` 新增 `@app.after_request` 中间件，自动记录 `/api/*` 事件到 `user_events`（排除 `/api/auth/` 和 `/api/analytics/`）
- [x] 1.3 Factory 中间件实现 FUNCTION_MAP 路径归类逻辑（按键长度降序匹配，未匹配归为"其他"）
- [x] 1.4 Factory 中间件计算 `duration_ms`（请求开始到 after_request 的时间差）
- [x] 1.5 Factory 新增数据清理逻辑：每天首次请求时检查并删除 90 天前的 `user_events` 记录
- [x] 1.6 验证：curl 多个 API 端点后查询 `user_events` 表确认事件正确记录

## 2. 聚合分析 API

- [x] 2.1 Factory 新增 `GET /api/analytics/overview` — 返回 DAU/MAU/今日事件数/最热门功能
- [x] 2.2 Factory 新增 `GET /api/analytics/functions?days=30` — 功能使用排行（名称、次数、占比）
- [x] 2.3 Factory 新增 `GET /api/analytics/users?days=30` — 用户活跃度排名（最近活跃、功能数、总调用、日均）
- [x] 2.4 Factory 新增 `GET /api/analytics/trends?days=30` — 活跃度趋势（按天的 DAU + 总调用量）
- [x] 2.5 Factory 新增 `GET /api/analytics/cold-hot?days=30` — 功能冷热图矩阵数据
- [x] 2.6 所有 analytics API 添加 admin 权限校验（非 admin 返回 403）
- [x] 2.7 验证：curl 各 analytics 端点返回正确聚合数据

## 3. 运营分析看板

- [x] 3.1 设置页新增"📊 运营分析"子 Tab（仅 admin 可见，排在用户管理之后）
- [x] 3.2 顶部 4 个指标卡片：DAU / MAU / 今日事件数 / 最热门功能
- [x] 3.3 功能使用排行：ECharts 水平柱状图 + 时间范围选择器（7天/30天/全部）
- [x] 3.4 活跃度趋势：ECharts 双 Y 轴折线图（DAU + 总调用量）
- [x] 3.5 用户活跃度表格：用户名、最近活跃、功能数、总调用、日均、不活跃标红
- [x] 3.6 功能冷热图：用户×功能矩阵，颜色深浅表示使用频次
- [x] 3.7 验证：admin 登录后查看运营分析看板，确认所有图表正确渲染

## 4. 验收与提交

- [x] 4.1 多用户场景测试：不同用户访问不同功能，看板数据正确区分
- [x] 4.2 性能测试：中间件对 API 响应时间影响 < 5ms
- [x] 4.3 权限测试：viewer/editor 访问 /api/analytics/* 返回 403
- [x] 4.4 所有变更提交并推送到远端
