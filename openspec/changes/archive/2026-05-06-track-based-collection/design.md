## Context

当前系统架构：

- **任务驱动**: `scheduled_tasks` 表以 `subject`（字符串）为核心，创建时手动指定 subject + sources
- **关键词过滤**: `_crawl_and_filter()` 中用 subject 匹配 `track_keywords` 表的 track_name 来获取关键词
- **入库**: 资讯存入 `financial_news` 表，subject 字段记录主题，metadata JSON 中有 relevance_score 等信息
- **赛道**: `tracks` 表（在 `financial_news.db`）有 5 条记录，与采集任务无直接关联
- **查询**: 前端按 track name 查 subject 字段来获取赛道资讯（`track_routes.py` 的 `get_track_news`）

核心矛盾：subject 是"搜索词"，track 是"用户关注的领域"，两者概念不同但目前耦合在一起。

## Goals / Non-Goals

**Goals:**
- 任务可通过 track_id 创建，系统自动从 track 获取 subject name、默认 sources、关键词
- 采集时用赛道所有关键词做 OR 过滤，记录每条资讯命中的具体关键词
- 支持按关键词查询资讯（一条资讯可能命中多个关键词）
- 一条资讯可关联多个赛道（通过关键词重叠）
- 向后兼容现有任务

**Non-Goals:**
- 不做关键词权重/评分（MVP 只有命中/未命中）
- 不改 financial_news 表的现有列结构
- 不做关键词自动推荐
- 不做前端 UI

## Decisions

### D1: scheduled_tasks 加 track_id 而非替换 subject

**选择**: `scheduled_tasks` 表新增 `track_id INTEGER NULL` 列，subject 保留
**理由**: track_id 是可选的关联字段。现有任务（核电等自定义主题）没有对应 track，继续用 subject 驱动。有 track_id 的任务，subject 自动取 track.name
**备选**: 强制所有任务必须有 track_id — 灵活性太差，用户自定义主题（如"核电"）无法归入现有赛道

### D2: news_keywords 关联表而非 metadata JSON

**选择**: 新建 `news_keywords(news_id, track_id, keyword)` 表
**理由**: 需要按关键词高效查询资讯（WHERE keyword=?），JSON 内的数组无法建索引。同时 track_id 列支持按赛道查关键词分布
**备选**: 在 financial_news.metadata 中存 matched_keywords JSON — 查询效率差，无法做 JOIN 聚合

### D3: 关键词匹配改为记录命中词而非纯过滤

**选择**: `_crawl_and_filter()` 改为：先计算每条资讯命中的关键词列表，未命中任何关键词的过滤掉，命中的保留并在入库时写入 news_keywords
**理由**: 这同时实现了过滤（未命中→丢弃）和标签（命中→记录具体词）两个需求，一次遍历完成
**备选**: 先过滤再单独跑一轮标签 — 重复计算

### D4: 跨赛道关键词命中

**选择**: 一条资讯入库时，检查所有赛道的所有关键词（不仅仅是当前任务的赛道），跨赛道命中也写入 news_keywords
**理由**: "碳纤维复合材料用于新能源汽车"同时属于碳纤维和新材料赛道。如果只记录当前赛道的命中，另一个赛道就查不到
**备选**: 只记录当前任务赛道的命中 — 实现简单但数据不完整
**取舍**: MVP 阶段先只记录当前任务赛道的命中（简化实现），跨赛道命中作为后续迭代

### D5: 按关键词查询 API

**选择**: `GET /api/news?keyword=钙钛矿` 查 news_keywords 表 JOIN financial_news，返回含该关键词的所有资讯
**理由**: 独立于 track 的查询维度。用户可能想看"所有含石墨烯的资讯"而不限定赛道
**备选**: 只通过 track 查询 — 不够灵活，用户明确要求按关键词查询

## Risks / Trade-offs

- **[风险] news_keywords 表膨胀** → 每条资讯 × 每个命中关键词一条记录。预估日均 50 条资讯 × 平均 3 个关键词 = 150 条/天，一年 5 万条，SQLite 完全能承受
- **[风险] 关键词匹配逻辑变更可能影响现有过滤效果** → 保持 OR 逻辑不变，只是额外记录命中词。先关键词过滤 → 再 LLM 评分的流程不变
- **[取舍] MVP 不做跨赛道匹配** → 当前任务只关联一个赛道，只记录该赛道的关键词命中。跨赛道命中需要全量关键词扫描，后续迭代
