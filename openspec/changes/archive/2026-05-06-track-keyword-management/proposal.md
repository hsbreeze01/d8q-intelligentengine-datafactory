## Why

当前赛道关键词管理只能通过后端 API（curl POST /api/tracks/{id}/keywords）操作，没有前端界面。用户需要直接调用 API 或修改数据库来增删关键词，门槛高且容易出错。随着采集任务以赛道为核心驱动，关键词管理成为日常高频操作，需要一个可视化的管理界面。

## What Changes

- 在任务管理页面的采集任务区域，为每个关联了赛道的任务增加"管理关键词"入口
- 新增关键词管理模态框：显示赛道当前所有关键词（标签列表），支持添加新关键词、删除已有关键词
- Factory `app.py` 补全代理路由：`POST /api/proxy/tracks/{id}/keywords`（添加）、`DELETE /api/proxy/tracks/{id}/keywords`（删除）
- 操作后实时刷新关键词列表和采集任务列表

## Capabilities

### New Capabilities
- `keyword-management-ui`: 赛道关键词可视化管理界面，包括关键词列表展示、添加新关键词、删除已有关键词的完整 CRUD 交互

### Modified Capabilities
<!-- 无需修改已有 spec，所有变更都是新增 -->

## Impact

- **前端**: `templates/index.html` 中的任务管理区域（loadTasks、新增管理关键词弹窗函数）
- **后端（Factory）**: `app.py` 新增 POST/DELETE 代理路由转发到 data-agent
- **后端（Data-agent）**: 已有 `POST /api/tracks/{id}/keywords` 和 `DELETE /api/tracks/{id}/keywords` API，无需修改
- **用户体验**: 用户可在界面直接管理赛道关键词，无需命令行操作
