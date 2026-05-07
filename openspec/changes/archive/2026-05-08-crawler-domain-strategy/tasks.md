## 1. 数据库变更

- [ ] 1.1 tracks 表新增 `default_sources TEXT` 列，默认 NULL
- [ ] 1.2 新建 `track_keywords` 表（id, track_id, keyword, UNIQUE(track_id, keyword)）
- [ ] 1.3 更新 tracks 数据：新材料/碳纤维 → default_sources 设为材料源列表，其余保持 NULL
- [ ] 1.4 将 `runner.py` 中硬编码的 TRACK_KEYWORDS 作为种子数据插入 track_keywords 表

## 2. 关键词 API

- [ ] 2.1 在 `api/track_routes.py` 新增 `GET /api/tracks/{track_id}/keywords` 端点
- [ ] 2.2 新增 `POST /api/tracks/{track_id}/keywords` 端点（添加关键词，含长度和数量校验）
- [ ] 2.3 新增 `DELETE /api/tracks/{track_id}/keywords/{keyword}` 端点
- [ ] 2.4 验证 API 端点功能（增删查）

## 3. 调度层适配

- [ ] 3.1 修改 `multi_source_crawl.py` 的 `crawl_all_sources()`：当 sources 为空时，从 tracks 表的 default_sources 列获取源列表
- [ ] 3.2 修改 `POST /api/tasks` 路由：sources 为空时，从 subject 对应的 track 自动填充 default_sources
- [ ] 3.3 将 `multi_source_crawl.py` 的 `ACTIVE_SOURCES` 改为动态获取（从 tracks 表聚合所有 default_sources）

## 4. 关键词过滤改造

- [ ] 4.1 在 `multi_source_crawl.py` 的 `_crawl_and_filter()` 中，LLM 评分前增加 DB 关键词前置过滤
- [ ] 4.2 实现关键词过滤函数：从 track_keywords 表读取关键词，对文章标题做包含匹配
- [ ] 4.3 移除 `crawlers/material/runner.py` 中硬编码的 TRACK_KEYWORDS（改为从 DB 读取或直接由上层过滤）

## 5. 种子数据迁移与清理

- [ ] 5.1 实现 `_ensure_seed_keywords()` 函数：服务启动时检查 track_keywords 表是否为空，为空则插入种子数据
- [ ] 5.2 确认种子数据覆盖所有赛道的关键词（新材料 12 个、碳纤维 9 个等）

## 6. 端到端验证

- [ ] 6.1 验证现有任务（核电/sources 显式指定）不受影响
- [ ] 6.2 创建无 sources 的新任务，验证自动从 track 获取 default_sources
- [ ] 6.3 手动执行任务，验证关键词过滤生效（日志可见过滤数量）
- [ ] 6.4 通过 API 添加新关键词，再次执行验证新关键词生效

## 7. 提交

- [ ] 7.1 提交并推送所有变更
