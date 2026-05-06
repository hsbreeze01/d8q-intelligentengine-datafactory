## 1. Cron 友好展示（前端）

- [x] 1.1 在 `index.html` 中添加 `cronToLabel(cron)` 函数，实现 cron→中文映射表（7 种预设模式 + fallback 原始值）
- [x] 1.2 修改 `loadTasks` 函数中采集任务表格的频率列，将 `${t.cron_expr||''}` 替换为 `${cronToLabel(t.cron_expr)}`
- [x] 1.3 修改 `loadTasks` 函数中创作/发布任务表格的频率列，将 `${t.freq}` 替换为友好的中文标签（daily→每日、weekly→每周、monthly→每月）

## 2. 采集任务编辑 API（data-agent 后端）

- [x] 2.1 在 `data-agent/api/routes.py` 中添加 `TaskUpdate` Pydantic 模型（subject/sources/cron_expr/max_results/track_id 均可选）
- [x] 2.2 在 `data-agent/api/routes.py` 中添加 `PUT /api/tasks/{task_id}` 端点：读取现有任务，合并非 None 字段，调用 save_task，重建调度器

## 3. 创作/发布任务编辑 API（factory 后端）

- [x] 3.1 在 `factory/app.py` 中添加 `PUT /api/content/tasks/<task_id>` 端点：读取 JSON 文件，按 id 定位任务，合并请求字段后写回

## 4. 采集任务编辑 UI（前端）

- [x] 4.1 在 `index.html` 任务列表中为每个采集任务行添加"编辑"按钮（在"执行"按钮前）
- [x] 4.2 添加 `editCollectForm(taskId)` 函数：获取任务详情，弹出与 showCollectForm 相同的 modal 结构，预填充当前值，赛道模式下禁用主题和来源编辑
- [x] 4.3 修改 `saveCollect()` 函数支持编辑模式：根据 window._editTaskId 是否存在决定调用 POST（新建）或 PUT（编辑）
- [x] 4.4 在 `index.html` 中添加 Factory 代理路由 `PUT /api/tasks/{task_id}` 转发到 data-agent

## 5. 创作/发布任务编辑 UI（前端）

- [x] 5.1 在 `index.html` 任务列表中为每个创作/发布任务行添加"编辑"按钮
- [x] 5.2 添加 `editContentForm(taskId)` 函数：获取任务详情，弹出与 showContentForm 相同的 modal 结构，预填充当前值
- [x] 5.3 修改 `saveContent()` 函数支持编辑模式：根据 window._editContentId 是否存在决定调用 POST（新建）或 PUT（编辑）

## 6. 测试验证

- [x] 6.1 验证频率列展示：确认采集任务显示中文频率，创作/发布任务显示中文频率
- [x] 6.2 验证采集任务编辑：编辑主题/来源/频率/最大数，确认保存成功且调度更新
- [x] 6.3 验证赛道采集任务编辑：确认主题和来源不可编辑，频率和最大数可编辑
- [x] 6.4 验证创作任务编辑：编辑主题/风格/频率/时间，确认保存成功
- [x] 6.5 验证发布任务编辑：编辑主题/渠道/频率/时间，确认保存成功
