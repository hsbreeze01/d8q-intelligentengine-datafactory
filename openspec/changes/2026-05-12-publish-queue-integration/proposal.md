# Proposal: Publish Queue Integration — factory scheduler 非阻塞改造

## Summary
factory scheduler 和 app.py 的 publish 流程从同步阻塞调用 `POST /api/publish` 改为异步投递 `POST /api/publish/queue`，配合 infopublisher 侧新增的队列系统。

## Motivation
infopublisher 已新增发布队列系统（openspec change: `2026-05-12-publish-queue`）。factory 需要配合改造：
- scheduler `_run_task()` publish 分支当前同步阻塞 50-75s
- 投递到队列后可立即返回，scheduler 主循环释放
- 通过轮询机制获取最终结果

## Expected Behavior
1. `_run_task()` publish 分支改调 `POST /api/publish/queue`，timeout 从 180s 降至 15s
2. 新增 `_poll_pending()` 每 60s 轮询已投递任务的完成状态
3. `app.py` `run_content_task()` publish 分支改调队列接口
4. exec_log 准确记录 publish 最终结果

## Files to Modify
1. `scheduler.py` — _run_task 改造 + _poll_pending + _append_scheduler_exec_log
2. `app.py` — run_content_task publish 分支改用 /api/publish/queue

## Constraints
- infopublisher 队列系统必须先部署完成
- 现有手动触发 publish 的行为不变（只是 API 路径变了）
- creation 任务逻辑不变
