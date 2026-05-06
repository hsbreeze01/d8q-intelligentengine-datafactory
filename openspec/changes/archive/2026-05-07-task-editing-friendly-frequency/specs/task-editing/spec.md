## ADDED Requirements

### Requirement: 采集任务编辑 API
系统 SHALL 提供 `PUT /api/tasks/{task_id}` 端点，允许修改已创建采集任务的参数。请求体 SHALL 支持可选字段：`subject`、`sources`、`cron_expr`、`max_results`、`track_id`。仅提交的字段 SHALL 被更新，未提交的字段保持不变。

#### Scenario: 编辑自定义采集任务
- **WHEN** 用户发送 PUT 请求到 `/api/tasks/{task_id}`，body 包含 `{"cron_expr": "0 */4 * * *", "max_results": 30}`
- **THEN** 系统 SHALL 更新该任务的 cron_expr 和 max_results，保留原有 subject 和 sources 不变，返回更新后的完整任务对象

#### Scenario: 编辑赛道采集任务
- **WHEN** 用户编辑 track_id 关联的赛道采集任务，仅修改 cron_expr 和 max_results
- **THEN** 系统 SHALL 更新频率和最大采集数，保留 track_id 和自动填充的 sources 不变

#### Scenario: 编辑不存在的任务
- **WHEN** 用户发送 PUT 请求到 `/api/tasks/{task_id}`，task_id 不存在
- **THEN** 系统 SHALL 返回 404 错误

#### Scenario: 编辑后调度器更新
- **WHEN** 任务的 cron_expr 被修改且任务处于 enabled 状态
- **THEN** 系统 SHALL 移除旧调度任务并使用新 cron_expr 添加新调度任务

### Requirement: 创作/发布任务编辑 API
系统 SHALL 提供 `PUT /api/content/tasks/{task_id}` 端点，允许修改已创建的创作或发布任务。请求体 SHALL 支持可选字段：`subject`、`style`（创作任务）、`channel`（发布任务）、`freq`、`run_at`。

#### Scenario: 编辑创作任务
- **WHEN** 用户发送 PUT 请求，body 包含 `{"style": "research_report", "freq": "weekly"}`
- **THEN** 系统 SHALL 更新风格和频率，返回更新后的任务对象

#### Scenario: 编辑发布任务
- **WHEN** 用户发送 PUT 请求，body 包含 `{"run_at": "09:00"}`
- **THEN** 系统 SHALL 更新执行时间，返回更新后的任务对象

#### Scenario: 编辑不存在的创作/发布任务
- **WHEN** 用户发送 PUT 请求，task_id 不存在
- **THEN** 系统 SHALL 返回 404 错误

### Requirement: 采集任务编辑 UI
任务列表中每个采集任务行 SHALL 显示"编辑"按钮。点击"编辑" SHALL 弹出与新建采集任务相同的表单 modal，但预填充该任务的当前值，标题显示为"📥 编辑采集任务"。

#### Scenario: 打开采集任务编辑表单
- **WHEN** 用户点击某个采集任务的"编辑"按钮
- **THEN** 系统 SHALL 弹出 modal，预填充该任务的 subject、sources（checkbox）、cron_expr（select）、max_results，并根据 track_id 自动切换到赛道/自定义模式

#### Scenario: 保存采集任务编辑
- **WHEN** 用户修改参数后点击"保存"
- **THEN** 系统 SHALL 调用 PUT API 更新任务，关闭 modal，刷新任务列表

#### Scenario: 赛道采集任务编辑限制
- **WHEN** 用户编辑赛道采集任务（track_id 存在）
- **THEN** 主题字段和数据来源区域 SHALL 不可编辑（灰色显示），仅频率和最大采集数可修改

### Requirement: 创作/发布任务编辑 UI
任务列表中每个创作/发布任务行 SHALL 显示"编辑"按钮。点击"编辑" SHALL 弹出与新建创作/发布任务相同的表单 modal，预填充当前值，标题显示为"✍️ 编辑创作任务"或"📤 编辑发布任务"。

#### Scenario: 打开创作任务编辑表单
- **WHEN** 用户点击某个创作任务的"编辑"按钮
- **THEN** 系统 SHALL 弹出 modal，预填充该任务的 subject、style、freq、run_at

#### Scenario: 打开发布任务编辑表单
- **WHEN** 用户点击某个发布任务的"编辑"按钮
- **THEN** 系统 SHALL 弹出 modal，预填充该任务的 subject、channel、freq、run_at

#### Scenario: 保存创作/发布任务编辑
- **WHEN** 用户修改参数后点击"保存"
- **THEN** 系统 SHALL 调用 PUT API 更新任务，关闭 modal，刷新任务列表
