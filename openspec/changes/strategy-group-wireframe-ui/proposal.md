# Proposal: 策略组 UI 按线框图重构

## Summary
按照 `Strategy_Group_UX_Wireframe.html` 线框图重构 DataFactory 策略组前端页面，实现完整的页面导航、角色分流和交互设计。

## Motivation
当前策略组前端存在以下问题：
1. **页面缺失**：线框图定义了 7 个页面，当前只实现了"我的策略"和"事件详情"（drawer 模式），缺少"策略发现"、"策略管理"、"策略组详情"、"回测"、"运行管理"
2. **交互不一致**：事件详情用 drawer 而非独立页面，缺少 ECharts 图表
3. **缺少角色分流**：线框图有 user/admin 两种视角，当前仅靠 `userRole` 变量简单控制
4. **事件卡片样式简单**：线框图有丰富的 event-card 样式（图标+指标+涨跌+lifecycle badge），当前是简单 div

## Target Pages (from Wireframe)

### 用户视角 (3 pages)
1. **策略发现** (`page-discover`) — 卡片网格 + 搜索/筛选 + 订阅/取消订阅
2. **我的策略** (`page-my`) — 已订阅策略组列表 + 活跃事件卡片
3. **事件详情** (`page-event`) — 3 tab（微观/宏观/信息关联）+ 生命周期管理

### 管理员视角 (4 pages)
4. **策略管理** (`page-list`) — 所有策略组卡片 + 搜索/筛选 + 新建按钮
5. **策略组配置** (`page-config`) — 编辑表单（已有部分实现）
6. **策略组详情** (`page-detail`) — 统计卡片 + 活跃事件 + 信号快照 + ECharts
7. **回测** (`page-backtest`) — ECharts 收益曲线 + 月度收益 + 统计摘要
8. **运行管理** (`page-run`) — 调度配置 + 时间线 + 运行历史

## Constraints
- 侧边栏不用考虑（用户明确要求）
- 融入现有 DataFactory SPA 架构（loadXxx(el) 模式）
- 事件详情从 drawer 改为全屏页面（或保持 drawer 但按线框图丰富内容）
- 前端是单体 `templates/index.html`，无构建工具
- CSS 使用内联 `<style>` 标签
- 不引入新框架，保持原生 JS + 已有的 ECharts CDN

## Expected Behavior
- 用户登录后根据角色看到不同页面
- 策略发现页展示所有可订阅策略组，支持搜索和类型筛选
- 事件详情页包含 3 个 tab（微观个股指标卡片、宏观板块趋势图表、信息关联+LLM分析）
- 管理员可管理策略组生命周期（创建/编辑/暂停/删除）
- 所有页面间导航流畅，面包屑正确
