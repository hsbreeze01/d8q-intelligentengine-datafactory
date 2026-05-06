## 1. 数据库变更

- [x] 1.1 `task_store.db` 的 `scheduled_tasks` 表新增 `track_id INTEGER NULL` 列
- [x] 1.2 `financial_news.db` 新建 `news_keywords` 表（id, news_id, track_id, keyword, UNIQUE(news_id, keyword)）
- [x] 1.3 在 `_store()` 函数中，资讯写入 financial_news 后，检查 metadata.matched_keywords 并写入 news_keywords

## 2. 任务创建支持 track_id

- [x] 2.1 修改 `TaskCreate` 模型：新增 `track_id: Optional[int] = None`
- [x] 2.2 修改 `POST /api/tasks`：当 track_id 存在时，查 tracks 表获取 name 作为 subject，获取 default_sources 作为 sources
- [x] 2.3 修改 `save_task()`：保存 track_id 到 scheduled_tasks 表
- [x] 2.4 修改 `_row_to_dict()`：解析 track_id 字段
- [x] 2.5 验证：通过 track_id=3 创建新材料任务，确认 subject/sources 自动填充

## 3. 关键词过滤改为记录命中词

- [x] 3.1 修改 `_crawl_and_filter()` 中的关键词过滤逻辑：从纯布尔过滤改为返回每条 item 命中的关键词列表
- [x] 3.2 将命中词列表存入 `item.metadata["matched_keywords"]`
- [x] 3.3 `_crawl_and_filter()` 接受可选 `track_id` 参数，有 track_id 时从 track_keywords 表查关键词

## 4. 关键词标签入库

- [x] 4.1 修改 `_store()` 函数：入库后检查 data_items 的 metadata.matched_keywords，批量写入 news_keywords 表
- [x] 4.2 news_keywords 写入需关联 news_id（financial_news 表的自增 id）和 track_id

## 5. 按关键词查询 API

- [x] 5.1 新增 `GET /api/news` 端点，接受 `keyword` 和可选 `track_id` 参数
- [x] 5.2 查询 news_keywords JOIN financial_news，返回资讯列表
- [x] 5.3 验证：插入测试关键词 → 查询返回正确结果

## 6. 端到端验证

- [x] 6.1 通过 track_id=3 创建采集任务并手动执行
- [x] 6.2 检查 app.log 确认关键词过滤 + 命中词记录
- [x] 6.3 检查 news_keywords 表确认关键词标签写入
- [x] 6.4 通过 GET /api/news?keyword=钙钛矿 查询验证
- [x] 6.5 验证旧任务（无 track_id）仍正常运行

## 7. 提交推送

- [x] 7.1 提交并推送所有变更
