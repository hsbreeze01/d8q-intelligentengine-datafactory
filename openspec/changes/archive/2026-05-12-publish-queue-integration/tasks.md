# Tasks: Publish Queue Integration

## 1. app.py — publish 路径改造

- [x] **1.1** 修改 `run_content_task()` 中 publish 分支（约 L998）：
  - `_publisher_request("POST", "/api/publish/queue", pub_data, max_retries=0)` 替代 `/api/publish`
  - 返回值改为 `{task_id, status: "queued"}` 格式
  - 不再等待发布完成，投递成功即返回 200

## 2. scheduler.py — 非阻塞改造

- [x] **2.1** 修改 `_run_task()` 中 publish 分支的 timeout 从 180s 改为 15s

- [x] **2.2** 修改 `_run_task()` publish 成功后的处理：
  - 解析返回的 `{task_id, status: "queued"}`
  - 在 task dict 中保存 `queue_task_id` 和 `queue_status`

- [x] **2.3** 新增 `_poll_pending()` 函数：
  - 遍历 tasks，找 `queue_status == "queued"` 的 publish 任务
  - 对每个调用 `GET http://127.0.0.1:8089/api/publish/queue/{queue_task_id}`
  - completed → 更新 queue_status，写入 exec_log
  - failed → 更新 queue_status，写入 exec_log（标记失败）
  - queued/running → 等待下次轮询

- [x] **2.4** 新增 `_append_scheduler_exec_log()` 辅助函数：
  - 写入 exec_log.json，格式与手动触发一致

- [x] **2.5** 在 `_tick()` 中调用 `_poll_pending()`：
  - 放在执行新任务之前

## 3. 验证

- [x] **3.1** 重启 factory 服务
- [x] **3.2** 手动触发一个 publish 任务验证全链路
- [x] **3.3** 检查 scheduler.log 确认 _tick 耗时降至 <5s
