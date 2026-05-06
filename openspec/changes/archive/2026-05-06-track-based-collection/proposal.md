## Why

当前采集任务以 `subject`（主题字符串）为核心驱动，而赛道（`tracks` 表）是独立的概念。两者之间没有正式关联——任务只靠 subject 字符串碰巧匹配 track_name 来间接获取关键词和默认源。这导致三个具体问题：

1. **无法以赛道为单位创建任务**：用户想选"新材料"赛道来采集，但 API 只接受 subject 字符串，不认 track_id
2. **关键词无法回标到资讯**：文章入库后只有 subject（如"新材料"），没有记录它命中了哪个具体关键词（如"钙钛矿"）。无法按关键词查询"所有含钙钛矿的资讯"
3. **一条资讯可能属于多个赛道**：标题含"碳纤维复合材料用于新能源汽车"的文章，同时属于"碳纤维"和"新材料"两个赛道，但当前只存一个 subject

用户需要：选赛道 → 系统用该赛道所有关键词（OR 关系）采集 → 每条资讯打上命中的关键词标签 → 后续按赛道或关键词均可查询。

## What Changes

- `scheduled_tasks` 表新增 `track_id INTEGER` 列（可选），创建任务时可指定赛道而非手动填 subject/sources
- 采集过滤时，按 track_id 查询该赛道所有关键词，标题包含任一关键词即通过（OR 关系）
- 入库时，每条资讯在 metadata 中记录命中的关键词列表（`matched_keywords`）
- 新增 `news_keywords` 关联表：一条资讯 × 多个关键词的 M:N 关系，支持按关键词精确查询
- 一条资讯可同时命中多个赛道的关键词，此时在 `news_keywords` 表中分别记录，每条关联带 track_id
- 新增 API：按关键词查询资讯 `GET /api/news?keyword=钙钛矿`

## Capabilities

### New Capabilities
- `track-driven-task`: 以赛道为驱动的采集任务——任务通过 track_id 关联赛道，自动获取默认源和关键词
- `keyword-tagging`: 资讯关键词标签——采集时记录每条资讯命中的具体关键词，支持按关键词查询

### Modified Capabilities

## Impact

- **数据库**: `task_store.db` 的 `scheduled_tasks` 表加 `track_id` 列；`financial_news.db` 新增 `news_keywords` 表
- **核心代码**: `multi_source_crawl.py`（关键词匹配逻辑改为记录命中词而非只做布尔过滤）、`routes.py`（任务创建支持 track_id）
- **存储层**: `financial_news_storage.py` 或入库逻辑需额外写入 `news_keywords` 表
- **API**: 新增 `GET /api/news?keyword=` 端点；`POST /api/tasks` 支持 `track_id` 参数
- **向后兼容**: 现有无 track_id 的任务继续按 subject 逻辑运行，不受影响
