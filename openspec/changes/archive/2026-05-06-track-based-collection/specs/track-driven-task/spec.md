## ADDED Requirements

### Requirement: Task creation with track_id
`scheduled_tasks` 表 SHALL 新增 `track_id INTEGER NULL` 列。`POST /api/tasks` 接受可选的 `track_id` 参数。当提供 track_id 时，系统自动从 tracks 表获取 subject name 和 default_sources。

#### Scenario: Create task with track_id
- **WHEN** POST /api/tasks body={"track_id": 3, "cron_expr": "0 7 * * *"}
- **THEN** 系统查询 tracks 表 id=3 → name="新材料"
- **AND** 自动设置 subject="新材料"
- **AND** 自动设置 sources=["sciencedaily","azom","sciencenet","cailiaoniu","asn","materials"]（从 `_TRACK_DEFAULT_SOURCES` 映射）

#### Scenario: Create task without track_id (backward compat)
- **WHEN** POST /api/tasks body={"subject": "核电", "sources": ["cailianshe","nbd"], "cron_expr": "0 */2 * * *"}
- **THEN** 行为与改动前完全一致，track_id 为 NULL

#### Scenario: track_id not found
- **WHEN** POST /api/tasks body={"track_id": 999}
- **THEN** 返回 400 错误，"赛道不存在"

### Requirement: Track-driven keyword lookup
当任务有 track_id 时，关键词过滤 SHALL 使用该 track_id 对应的赛道关键词（从 track_keywords 表），而非通过 subject 字符串匹配 track_name。

#### Scenario: Keywords via track_id
- **WHEN** 任务 track_id=3（新材料），执行采集
- **THEN** 从 track_keywords 表查询 track_name="新材料" 的所有关键词
- **AND** 用这些关键词对文章标题做 OR 匹配过滤

#### Scenario: Keywords via subject (backward compat)
- **WHEN** 任务无 track_id（旧任务），subject="新材料"
- **THEN** 保持现有行为，通过 subject 匹配 track_name 查关键词

### Requirement: crawl_all_sources accepts track_id
`crawl_all_sources()` 函数 SHALL 新增可选参数 `track_id: Optional[int]`。当 track_id 存在时，优先从 tracks 表获取默认源和关键词。

#### Scenario: crawl with track_id
- **WHEN** crawl_all_sources(subject="新材料", track_id=3)
- **THEN** 从 _TRACK_DEFAULT_SOURCES 映射获取 sources
- **AND** 从 track_keywords 表查 track_name 查关键词
