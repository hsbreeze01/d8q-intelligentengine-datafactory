## Context

当前爬虫调度架构：

- `multi_source_crawl.py` 的 `crawl_all_sources()` 接收 `sources` 列表，硬编码 `_CRAWL_MAP` 映射 4 个源
- `tools/materials_crawler.py` 和 `crawlers/material/runner.py` 各自硬编码 `TRACK_KEYWORDS` 字典
- `tracks` 表有 5 条赛道记录，与爬虫源和关键词均无关联
- 定时任务表 `scheduled_tasks` 的 `sources` 字段由前端手动指定

用户期望：选赛道 → 系统自动知道用什么源、按什么关键词过滤，且用户可以持续补充关键词。

## Goals / Non-Goals

**Goals:**
- 赛道有默认数据源，创建任务时无需手动填 sources
- 赛道关键词用户可配置（增/删），不依赖代码部署
- 关键词过滤在入库前生效，只存相关内容
- 改动最小化——不新建模块体系，只加表 + 改现有流程

**Non-Goals:**
- 不改存储层（EnhancedFinancialNewsStorage 和 financial_news 表不变）
- 不做源的健康检测、自动切换
- 不做前端 UI（本次只做后端 API + 调度逻辑）
- 不统一爬虫技术栈（HTTP/Crawl4AI/Playwright 各源保持现状）

## Decisions

### D1: tracks 表加列而非新建配置表

**选择**: tracks 表新增 `default_sources TEXT` 列（JSON 数组格式）
**理由**: 赛道和默认源是 1:1 关系，放同一行最简单，避免 JOIN。初始值：`["cailianshe","nbd"]`（通用）/ `["sciencedaily","azom","sciencenet","cailiaoniu","asn"]`（材料）
**备选**: 新建 domain_strategies 表 — 过度设计，赛道只有 5 个

### D2: track_keywords 独立表

**选择**: 新建 `track_keywords(track_id, keyword)` 表
**理由**: 关键词与赛道是 M:N 关系（一个赛道多关键词，同一关键词可能属于多赛道），独立表支持灵活查询和去重
**备选**: tracks 表加 JSON 列 — 查询不便，用户增删单个关键词需读改写整个 JSON

### D3: 关键词过滤位置——爬取后、入库前

**选择**: 在 `_crawl_and_filter()` 中，LLM 相关性评分之前先用关键词做快速过滤
**理由**: 已有 `relevance_scorer.py` 做 LLM 过滤，关键词是更轻量的前置过滤，减少送 LLM 的数据量。先关键词过滤 → 再 LLM 评分 → 入库
**备选**: 只用 LLM 过滤不用关键词 — 成本高、延迟大，关键词是免费的前置筛选

### D4: 初始关键词从代码迁移到 DB

**选择**: 将 `runner.py` 的 `TRACK_KEYWORDS` 和 `materials_crawler.py` 中的关键词作为种子数据一次性迁移到 `track_keywords` 表
**理由**: 迁移后代码中的硬编码关键词可以移除，全部走 DB。现有行为不变（关键词一样），但变得用户可配置。

## Risks / Trade-offs

- **[风险] 用户添加泛化关键词导致噪音** → API 层做关键词长度/数量限制（最少 2 字，每赛道最多 50 个），过滤效果在执行日志中可见
- **[风险] 关键词表和代码关键词并存期混乱** → 一次性迁移，迁移后删除代码中硬编码，不存在并存期
- **[取舍] 不做关键词分组（包含/排除）** → MVP 只做包含匹配（标题含关键词即相关），排除和权重等后续迭代
