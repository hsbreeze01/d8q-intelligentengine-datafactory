## Why

后端已支持以 track_id 创建采集任务（`POST /api/tasks {track_id: 3}`），系统自动获取赛道名称、默认数据源和关键词。但前端任务创建界面（`tasks.html`）仍只有"采集主题"文本输入框和硬编码的 4 个数据源复选框。用户无法通过选择赛道来创建任务，也不知道赛道有哪些关键词。

需要在前端任务创建流程中增加赛道维度，让用户选赛道即可自动填充主题和数据源，并展示该赛道的关键词列表。

## What Changes

- 采集任务创建弹窗新增"赛道"下拉选择器（可选），列出所有 active 赛道
- 选择赛道后自动填充主题（subject）和数据源（sources），主题变为只读
- 赛道选择后在表单中展示该赛道的关键词标签列表，让用户了解采集范围
- 用户可切换回"自定义主题"模式（不选赛道），此时主题和数据源恢复手动输入
- 保存时若选了赛道，提交 `track_id` 字段到后端 API
- 任务列表中显示赛道标签（colored badge），区分赛道任务和自定义任务

## Capabilities

### New Capabilities
- `track-task-form`: 采集任务创建表单的赛道选择模式——选择赛道后自动填充主题和数据源，展示关键词范围

### Modified Capabilities

## Impact

- **前端**: `templates/tasks.html` — 采集任务弹窗 UI 改造 + JS 逻辑变更
- **后端**: `app.py` 可能需要新增代理路由转发 `/api/tracks` 到 data-agent（如果 factory 无直接访问 track 列表的 API）
- **API 消费**: 前端需调用 data-agent 的 `GET /api/tracks` 和 `GET /api/tracks/{id}/keywords` 获取赛道和关键词数据
