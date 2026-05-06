## Why

用户创建采集、创作、发布任务后无法修改任何参数（主题、来源、频率等），只能删除重建。频率列直接显示 cron 表达式（如 `0 */2 * * *`），非技术用户无法理解含义。需要提供任务编辑功能和用户友好的频率展示。

## What Changes

- 为采集任务添加编辑功能：支持修改主题、数据来源、调度频率、最大采集数
- 为创作/发布任务添加编辑功能：支持修改主题、风格/渠道、频率、执行时间
- 频率展示友好化：将 cron 表达式转换为中文描述（如"每2小时"、"工作日每天1次"）
- 采集任务新建表单中的频率选择器改为更友好的展示方式（已用 select，保持一致）
- 任务列表中"操作"列增加"编辑"按钮

## Capabilities

### New Capabilities
- `task-editing`: 采集任务和创作/发布任务的编辑功能，包含后端 API 和前端 UI
- `cron-friendly-display`: cron 表达式到中文友好描述的转换，用于任务列表频率列展示

### Modified Capabilities

## Impact

- **Factory 前端** (`templates/index.html`): loadTasks 函数（频率列渲染 + 编辑按钮）、新增 editCollectForm/editContentForm 函数、新增 cronToLabel 转换函数
- **Data-agent API** (`api/routes.py`): 新增 PUT /tasks/{task_id} 端点，新增 TaskUpdate 模型
- **Factory API** (`app.py`): 新增 PUT /api/content/tasks/{task_id} 端点
- **Task Store** (`storage/task_store.py`): 无需改动（save_task 已支持 upsert）
- **无数据库 schema 变更**
