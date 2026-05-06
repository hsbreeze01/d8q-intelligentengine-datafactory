## ADDED Requirements

### Requirement: Track keywords database table
系统 SHALL 提供 `track_keywords` 表，存储赛道与关键词的映射关系。表结构：`id INTEGER PRIMARY KEY, track_id INTEGER REFERENCES tracks(id), keyword TEXT NOT NULL, UNIQUE(track_id, keyword)`。

#### Scenario: Query keywords for a track
- **WHEN** 系统查询 track_id=3（新材料）的关键词
- **THEN** 返回 ["新材料", "材料科学", "钙钛矿", "石墨烯", ...] 等该赛道所有关键词

### Requirement: Keyword CRUD API
系统 SHALL 提供 REST API 端点管理赛道关键词。

#### Scenario: List keywords for a track
- **WHEN** GET /api/tracks/{track_id}/keywords
- **THEN** 返回该赛道所有关键词列表

#### Scenario: Add keyword to track
- **WHEN** POST /api/tracks/{track_id}/keywords body={"keyword": "钙钛矿"}
- **THEN** 系统将关键词添加到该赛道，重复关键词忽略
- **AND** 返回更新后的关键词列表

#### Scenario: Delete keyword from track
- **WHEN** DELETE /api/tracks/{track_id}/keywords/{keyword}
- **THEN** 系统移除该关键词，返回更新后的关键词列表

### Requirement: Keyword validation
系统 SHALL 对关键词做基本校验：最少 2 个字符，每赛道最多 50 个关键词。

#### Scenario: Reject too-short keyword
- **WHEN** 用户添加关键词 "a"（单字符）
- **THEN** 返回 400 错误，提示关键词长度不足

#### Scenario: Reject excess keywords
- **WHEN** 赛道已有 50 个关键词，用户尝试再添加
- **THEN** 返回 400 错误，提示超出上限

### Requirement: Keyword-based content filtering
系统在爬取数据后、入库前 SHALL 使用赛道关键词对文章标题做包含匹配过滤。标题中包含任一关键词的文章视为相关。

#### Scenario: Filter articles by keywords
- **WHEN** 新材料赛道关键词包含 ["钙钛矿", "石墨烯"]
- **AND** 爬取到标题 "新型钙钛矿太阳能电池效率突破 30%"
- **THEN** 该文章通过关键词过滤，进入后续 LLM 评分

#### Scenario: Filter out irrelevant articles
- **WHEN** 新材料赛道关键词包含 ["钙钛矿", "石墨烯"]
- **AND** 爬取到标题 "Giant Fossil Found in Garden Wall"
- **THEN** 该文章未命中任何关键词，被过滤掉

### Requirement: Seed keywords from existing code
系统 SHALL 在首次启动时将当前硬编码的 `TRACK_KEYWORDS` 迁移到 `track_keywords` 表作为种子数据。

#### Scenario: First startup migration
- **WHEN** data-agent 启动且 `track_keywords` 表为空
- **THEN** 系统从硬编码 `TRACK_KEYWORDS`（新材料、碳纤维等）自动填充到对应 track_id
