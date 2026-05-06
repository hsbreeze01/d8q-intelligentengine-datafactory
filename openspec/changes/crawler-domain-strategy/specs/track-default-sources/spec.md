## ADDED Requirements

### Requirement: Track default sources column
tracks 表 SHALL 新增 `default_sources TEXT` 列，存储该赛道的默认数据源 JSON 数组。NULL 表示使用系统默认 `["cailianshe", "nbd"]`。

#### Scenario: Track with configured sources
- **WHEN** track "新材料" 的 default_sources = '["sciencedaily","azom","sciencenet","cailiaoniu","asn"]'
- **THEN** 该赛道的任务自动使用这 5 个数据源

#### Scenario: Track without configured sources uses fallback
- **WHEN** track "人工智能" 的 default_sources = NULL
- **THEN** 使用系统默认源列表 ["cailianshe", "nbd", "weibo"]

### Requirement: Auto-fill sources on task creation
通过 API 创建定时任务时，若请求中 `sources` 为空或未指定，系统 SHALL 从任务 subject 对应的 track 的 `default_sources` 自动填充。

#### Scenario: Create task without sources
- **WHEN** POST /api/tasks body={"subject": "新材料", "cron_expr": "0 7 * * *"}
- **THEN** 系统查找 "新材料" track 的 default_sources
- **AND** 自动设置 sources=["sciencedaily","azom","sciencenet","cailiaoniu","asn"]

#### Scenario: Create task with explicit sources preserves them
- **WHEN** POST /api/tasks body={"subject": "核能", "sources": ["cailianshe","nbd"], "cron_expr": "0 */2 * * *"}
- **THEN** 系统使用用户指定的 sources，不覆盖

### Requirement: Backward compatible dispatch
`crawl_all_sources()` 函数 SHALL 保持现有签名不变，同时支持 sources 为空时自动解析。

#### Scenario: Existing calls with sources unchanged
- **WHEN** crawl_all_sources(subject="核能", sources=["cailianshe","nbd"])
- **THEN** 行为与改动前完全一致

#### Scenario: New calls without sources auto-resolve
- **WHEN** crawl_all_sources(subject="新材料", sources=None)
- **THEN** 从 track "新材料" 的 default_sources 获取源列表执行
