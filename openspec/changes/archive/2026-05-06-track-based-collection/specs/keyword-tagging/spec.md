## ADDED Requirements

### Requirement: news_keywords association table
系统 SHALL 提供 `news_keywords` 表存储资讯与关键词的关联。表结构：`id INTEGER PRIMARY KEY, news_id INTEGER REFERENCES financial_news(id), track_id INTEGER, keyword TEXT NOT NULL, UNIQUE(news_id, keyword)`。

#### Scenario: Insert keyword associations
- **WHEN** 一条资讯（news_id=100）标题 "新型钙钛矿太阳能电池效率突破30%" 通过关键词过滤
- **AND** 命中了 "钙钛矿" 和 "solar cell" 两个关键词
- **THEN** news_keywords 表新增两行：(news_id=100, track_id=3, keyword="钙钛矿"), (news_id=100, track_id=3, keyword="solar cell")

### Requirement: Record matched keywords during filtering
`_crawl_and_filter()` 在关键词过滤阶段 SHALL 记录每条通过过滤的 DataItem 命中的具体关键词列表，存入 `item.metadata["matched_keywords"]`。

#### Scenario: Keywords recorded in metadata
- **WHEN** 文章标题 "Graphene supercapacitor achieves record energy density"
- **AND** 赛道关键词包含 ["graphene", "supercapacitor", "ceramic"]
- **THEN** item.metadata["matched_keywords"] = ["graphene", "supercapacitor"]
- **AND** 该文章通过过滤（至少命中 1 个关键词）

#### Scenario: No keyword match - filtered out
- **WHEN** 文章标题 "Giant Fossil Found in Garden Wall"
- **AND** 赛道关键词包含 ["graphene", "supercapacitor"]
- **THEN** 无命中关键词，文章被过滤掉

### Requirement: Write news_keywords on storage
资讯入库时，如果 metadata 中有 `matched_keywords`，系统 SHALL 将每个关键词写入 `news_keywords` 表，关联 news_id 和当前 track_id。

#### Scenario: Storage writes keyword tags
- **WHEN** 一条资讯成功写入 financial_news 表（news_id=100）
- **AND** metadata.matched_keywords = ["钙钛矿", "perovskite"]
- **THEN** news_keywords 表写入两行记录

#### Scenario: No matched_keywords (backward compat)
- **WHEN** 一条资讯的 metadata 中没有 matched_keywords
- **THEN** 不写入 news_keywords 表，行为与改动前一致

### Requirement: Query news by keyword
系统 SHALL 提供 API 端点按关键词查询资讯。

#### Scenario: Search by keyword
- **WHEN** GET /api/news?keyword=钙钛矿
- **THEN** 查询 news_keywords 表中 keyword="钙钛矿" 的所有 news_id
- **AND** JOIN financial_news 返回完整资讯列表，按 publish_time DESC 排序

#### Scenario: Search with track filter
- **WHEN** GET /api/news?keyword=graphene&track_id=3
- **THEN** 只返回 track_id=3 赛道下 keyword="graphene" 的资讯

#### Scenario: No results
- **WHEN** GET /api/news?keyword=不存在的关键词
- **THEN** 返回空列表 {"items": [], "total": 0}
