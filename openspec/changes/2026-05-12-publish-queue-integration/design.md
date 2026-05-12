# Design: Publish Queue Integration — factory 侧

## Architecture Decision
最小改动原则：只换 URL 路径 + 新增轮询机制，不重构 scheduler 架构。

## Data Flow
```
scheduler _tick()
  │
  ├── _poll_pending()  ← 先轮询上次投递的结果
  │     GET /api/publish/queue/{task_id}
  │     └── completed → 写 exec_log
  │     └── failed → 写 exec_log
  │
  ├── _run_task(publish)
  │     POST /api/content/tasks/{id}/run
  │       └── app.py → POST /api/publish/queue → 返回 {task_id, status: "queued"}
  │     ← 立即返回（<1s）
  │
  └── _tick() 结束
```

## Files to Modify

| File | Change |
|------|--------|
| `scheduler.py` | `_run_task()` timeout 180→15s；新增 `_poll_pending()`；新增 `_append_scheduler_exec_log()` |
| `app.py` | `run_content_task()` publish 分支：`/api/publish` → `/api/publish/queue` |
