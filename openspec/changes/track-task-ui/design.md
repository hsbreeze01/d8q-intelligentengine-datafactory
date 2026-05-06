## Context

Factory 前端是 Flask + Jinja 渲染的单页 HTML（`templates/tasks.html`），使用原生 JavaScript + fetch API。采集任务创建弹窗当前有 4 个字段：主题（text input）、数据源（checkboxes）、调度频率（select）、最大采集数（number input）。

后端已支持：
- `POST /api/tasks` 接受 `track_id` 参数，自动填充 subject + sources
- `GET /api/tracks` 返回赛道列表（id, name, color, keywords）
- `GET /api/tracks/{id}/keywords` 返回赛道关键词列表

Factory 已有 proxy 机制：`/api/proxy/tracks` → data-agent `/api/tracks`。但缺少 `/api/tracks/{id}/keywords` 的代理。

## Goals / Non-Goals

**Goals:**
- 采集任务弹窗新增赛道选择器，选择后自动填充主题和数据源
- 展示赛道关键词列表，让用户了解采集范围
- 任务列表中标识赛道任务（带颜色标签）
- 提交时发送 track_id 到后端

**Non-Goals:**
- 不做关键词的增删操作（已有独立 API）
- 不改创作任务和发布任务的表单
- 不做赛道管理界面
- 不改后端调度逻辑

## Decisions

### D1: 赛道选择器用 select 下拉框

**选择**: 弹窗顶部新增"采集模式"切换（赛道 / 自定义），赛道模式显示赛道下拉框
**理由**: 保持与现有 UI 一致的 select 风格。赛道有 color 属性，option 前可以加色点
**备选**: 标签式切换（Tab） — 两个模式的表单差异不大，select 更紧凑

### D2: 选择赛道后主题和数据源变为只读

**选择**: 赛道模式下 subject input 和 sources checkboxes 禁用，自动从赛道填充
**理由**: 赛道任务的 subject 和 sources 由后端管理，前端不应覆盖
**备选**: 允许用户在赛道基础上微调 — 增加复杂度，且与后端逻辑不一致

### D3: 关键词展示用标签 chips

**选择**: 赛道下方展示关键词标签列表（与现有 kw-panel 风格一致）
**理由**: 用户需要知道"选了这个赛道会按哪些词采集"，chips 是最直观的方式
**备选**: 折叠面板 — 额外点击操作，不如直接展示

### D4: Factory 新增 keywords proxy 路由

**选择**: 在 app.py 的 proxy_tracks 路由中增加 `/api/proxy/tracks/<id>/keywords`
**理由**: 前端统一走 factory proxy，不需要知道 data-agent 地址
**备选**: 前端直接调用 data-agent — 跨域问题，且破坏代理架构

## Risks / Trade-offs

- **[风险] 赛道关键词列表过长（如新材料 30 个）** → 展示区域限高 120px + overflow scroll，或只显示前 10 个 + "更多" 展开
- **[风险] 切换赛道/自定义模式时已填数据丢失** → 切换前不清理，只在提交时取值。自定义模式下隐藏赛道相关 UI
- **[取舍] 不做"在赛道基础上添加自定义关键词"** → MVP 先做纯赛道模式，混合模式后续迭代
