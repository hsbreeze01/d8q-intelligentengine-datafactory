## Why

当前系统有两个断层：(1) 任务创建时需手动指定数据源技术标识（如 `["cailianshe","materials"]`），用户不应关心底层源；(2) 关键词过滤硬编码在 Python 代码中（`TRACK_KEYWORDS`），用户无法自行扩展。随着赛道扩展，需要一个简单的机制让系统根据赛道自动选择数据源，并让用户自定义哪些关键词属于该赛道。

## What Changes

- tracks 表新增 `default_sources` 列（JSON）：存储该赛道的默认数据源列表，任务创建时 sources 为空则自动取此值
- 新增 `track_keywords` 表：用户可配置的关键词 → 赛道映射，替代硬编码的 `TRACK_KEYWORDS`
- 新增 API 端点：用户可对赛道增删关键词
- 爬取调度流程微调：关键词过滤改用 DB 中的用户配置
- `multi_source_crawl.py` 微调：`sources` 为空时从 tracks 表的 `default_sources` 取值

## Capabilities

### New Capabilities
- `track-keyword-config`: 赛道关键词用户配置——用户可为每个赛道添加/删除关键词，系统按关键词过滤采集内容
- `track-default-sources`: 赛道默认数据源——tracks 表存储默认源列表，任务创建自动填充

### Modified Capabilities

## Impact

- **数据库**: tracks 表 ALTER 加列 + 新建 track_keywords 表
- **核心代码**: `multi_source_crawl.py`（sources 自动填充）、`tools/materials_crawler.py`（关键词来源改 DB）
- **API**: 新增 `GET/POST/DELETE /api/tracks/{id}/keywords` 端点
- **前端**: 赛道管理页增加关键词编辑区域（factory 侧，本次不涉及）
- **向后兼容**: 现有硬编码 TRACK_KEYWORDS 作为初始种子数据迁移到 DB，不再代码维护
