## Context

当前系统有三类任务管理 UI（采集、创作、发布），均支持创建、删除、启停、手动执行，但不支持编辑已创建任务的任何参数。频率信息以原始 cron 表达式（如 `0 */2 * * *`）直接展示，非技术用户无法理解。

技术栈：
- **采集任务**: FastAPI 后端 (`data-agent/api/routes.py`)，APScheduler 调度，SQLite 存储
- **创作/发布任务**: Flask 后端 (`factory/app.py`)，JSON 文件存储 (`data/content_tasks.json`)
- **前端**: 单一 SPA (`templates/index.html`)，通过 Factory proxy 调用后端 API

## Goals / Non-Goals

**Goals:**
- 用户可在任务列表中点击"编辑"修改已创建任务的参数
- 频率列展示中文描述而非 cron 表达式
- 编辑后立即生效（调度器更新）

**Non-Goals:**
- 不修改任务类型（采集→创作、创作→发布等不可变）
- 不修改任务 ID
- 不修改数据库 schema（task_store.save_task 已支持 upsert）
- 不改变 cron 表达式的内部存储格式

## Decisions

### 1. cron 友好展示方案：前端纯函数映射

**选择**: 前端 JS 实现 `cronToLabel(cron_expr)` 函数，通过预定义映射表转换已知模式，未知模式 fallback 显示原始 cron。

**替代方案**: 后端 API 返回 label 字段。但后端已存储 cron_expr，转换逻辑纯展示层关注点，无需改 API response schema。

映射表覆盖新建表单中所有选项：
| cron_expr | 中文标签 |
|-----------|----------|
| `0 */1 * * *` | 每小时 |
| `0 */2 * * *` | 每2小时 |
| `0 */4 * * *` | 每4小时 |
| `0 */6 * * *` | 每6小时 |
| `0 8,12,18 * * *` | 每天3次(8/12/18点) |
| `0 9 * * *` | 每天1次(9点) |
| `0 9 * * 1-5` | 工作日每天1次 |

### 2. 采集任务编辑 API：复用 save_task + 重建调度

**选择**: 新增 `PUT /api/tasks/{task_id}` 端点，接收 `TaskUpdate` 模型（与 `TaskCreate` 相同字段但均可选），调用已有 `task_store.save_task()` 覆盖写入，然后移除旧调度、添加新调度。

**理由**: task_store.save_task 已是 upsert 语义（按 id 覆盖），无需新增存储层方法。调度器也已提供 add_scheduled_job/remove_scheduled_job。

### 3. 创作/发布任务编辑：PUT 端点 + JSON 文件更新

**选择**: 新增 `PUT /api/content/tasks/<task_id>` 端点，读取 JSON 文件，按 id 定位任务，合并请求字段后写回。

### 4. 编辑 UI：复用新建表单的 modal 模式

**选择**: 编辑时弹出与新建相同的 modal，但预填充已有值，标题改为"编辑任务"，提交调用 PUT 端点。

**理由**: 避免新增大量 HTML 模板代码，复用已有表单结构。通过 `editCollectForm(taskId)` 和 `editContentForm(taskId)` 函数触发。

### 5. 赛道采集任务的编辑限制

**选择**: 赛道模式下主题、来源不可编辑（由赛道决定），仅可编辑频率和最大采集数。自定义模式下所有字段可编辑。

**理由**: 赛道采集的主题和来源由赛道配置自动填充，允许用户手动修改会导致与赛道不同步。

## Risks / Trade-offs

- **cron 映射表不覆盖自定义 cron** → fallback 显示原始表达式，用户仍可理解大部分场景。未来可扩展为 cron 解析器。
- **并发编辑 JSON 文件** → 创作/发布任务用文件存储，无锁机制。低频操作，风险可接受。
- **编辑调度中的任务** → 先移除旧调度再添加新调度，存在极短窗口期无调度。对于分钟级任务影响可忽略。
