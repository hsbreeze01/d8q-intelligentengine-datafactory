# Tasks: 策略组 UI 按线框图重构

## Group 1: 后端路由与 API 代理

- [ ] **1.1** 在 `compass_pages.py` 新增 3 个页面路由：策略组详情 (`/strategy/admin/groups/<id>/`)、回测页 (`/strategy/admin/groups/<id>/backtest/`)、运行管理页 (`/strategy/admin/groups/<id>/run/`)，每个路由调用 Compass API 获取数据并渲染对应模板
- [ ] **1.2** 在 `compass_pages.py` 新增 API 代理路由：策略组统计 (`/api/strategy/groups/<id>/stats/`)、回测数据 (`/api/strategy/groups/<id>/backtest/`)、运行历史 (`/api/strategy/groups/<id>/runs/`)、信号快照 (`/api/strategy/groups/<id>/signals/`)、手动触发执行 (`/api/strategy/groups/<id>/run/trigger/`)，统一通过 `_compass_request()` 代理

## Group 2: 用户页面模板重构

- [ ] **2.1** 重构 `templates/compass/strategy/discover.html` — 按线框图 page-discover 实现：4 统计卡片 + 搜索/筛选工具栏 + 卡片网格（含策略标签、订阅状态、交互按钮），移植线框图 `.group-card`/`.gc-*` CSS 类 `[scope: frontend]`
- [ ] **2.2** 重构 `templates/compass/strategy/my_strategies.html` — 按线框图 page-my 实现：4 统计卡片 + 按策略组分段布局 + 线框图 event-card 样式（图标+触发数+确认度+涨跌幅+lifecycle badge），空状态处理 `[scope: frontend]`
- [ ] **2.3** 重构 `templates/compass/strategy/event_detail.html` — 按线框图 page-event 实现三 Tab：微观数据（stock-snapshot-grid 卡片网格）、宏观数据（趋势聚合+板块走势 ECharts + 每日统计表）、信息关联（LLM 分析+关联资讯流），增加统计卡片区域和 lifecycle 管理条 `[scope: frontend]`

## Group 3: 管理员页面模板

- [ ] **3.1** 重构 `templates/compass/strategy/admin_list.html` — 将现有表格布局改为线框图卡片网格布局，增加 4 统计卡片和搜索/筛选工具栏，卡片包含编辑/暂停/激活/删除操作按钮 `[scope: frontend]`
- [ ] **3.2** 修改 `templates/compass/strategy/admin_edit.html` — 在现有表单底部增加"信号规则"区块（买入阈值输入 + 冷却期输入 + 关联策略表格增加权重/阈值可编辑列） `[scope: frontend]`
- [ ] **3.3** 新建 `templates/compass/strategy/admin_detail.html` — 按线框图 page-detail 实现：4 统计卡片 + 活跃事件列表 + 今日信号快照表格 + 近 7 日信号趋势 ECharts 柱状图，工具栏含回测/运行管理/编辑按钮 `[scope: frontend]`
- [ ] **3.4** 新建 `templates/compass/strategy/admin_backtest.html` — 按线框图 page-backtest 实现：6 格统计摘要 + 收益曲线 vs 基准 ECharts + 月度收益分布 ECharts，工具栏含时间范围选择和运行回测按钮 `[scope: frontend]`
- [ ] **3.5** 新建 `templates/compass/strategy/admin_run.html` — 按线框图 page-run 实现：4 统计卡片 + 调度配置表单 + 运行历史时间线组件，工具栏含暂停/立即执行按钮 `[scope: frontend]`

## Group 4: 基础设施与导航

- [ ] **4.1** 更新 `templates/compass/strategy/base.html` — 增加面包屑导航组件（top-bar 区域），增加线框图共用的 CSS 类（`.lifecycle-badge`、`.event-card`、`.toolbar`、`.tab-bar` 等），确保侧边栏导航项与所有新页面对应 `[scope: frontend]`
