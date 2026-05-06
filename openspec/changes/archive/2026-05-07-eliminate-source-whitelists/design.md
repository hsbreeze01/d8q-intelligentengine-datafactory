## Context

当前存储层有两道独立白名单（`financial_sources` 和 `financial_platforms`），与 DataSource 枚举不同步。新源注册到枚举后若未同步加入白名单，数据被静默丢弃。此外 INSERT 语句不包含 `news_type` 字段，导致新源数据永远无分类标签。

DataSource 枚举有 19 个成员，但只有 11-13 个在存储白名单中。6 个源（baidu/sina/sohu/tencent/weibo/xiaohongshu）注册在枚举中但无爬虫实现，未来实现后也会遇到同样的白名单问题。

## Goals / Non-Goals

**Goals:**
- 存储层不再维护独立白名单，任何 DataSource 枚举成员均可存储
- INSERT 时为 `news_type` 提供默认值，确保数据在各 Tab 可见
- 新增源步骤从 6 步降为 2 步（枚举 + crawl 函数）

**Non-Goals:**
- 不重构为重量级 SourceConfig 注册表（方案 B，后续按需）
- 不修改 DataSource 枚举本身的定义方式
- 不修改 ACTIVE_SOURCES 或 _CRAWL_MAP 的结构（它们解决不同问题：调度路由）
- 不处理 ai_summary 自动生成（独立 pipeline 问题）

## Decisions

### 1. 存储白名单移除策略：直接删除，用枚举验证替代

**选择**: 删除 `financial_sources` 和 `financial_platforms` 集合，存储层的 source 验证只依赖 `DataSource(source_value)` 是否抛 ValueError。

**理由**: 枚举已是唯一注册入口，白名单是冗余的第二道门。保留白名单的唯一理由是"防止未实现爬虫的源被存储"，但这不应由存储层负责——存储层只负责存数据。

### 2. news_type 默认值：INSERT 时设为 "tech"

**选择**: 在 `enhanced_financial_news_storage.py` 的 INSERT SQL 中增加 `news_type` 列，默认值为 `"tech"`。

**理由**: 5 个 tab 依赖 news_type 做过滤和展示。空值导致数据在 Feed 类型过滤、政策分析、热度统计中不可见。"tech" 是最安全的默认值——几乎所有资讯都适用。

**替代方案**: 在 DataItem 模型中增加 default_news_type 字段。但这需要修改所有爬虫的 DataItem 构造，改动面更大。

### 3. 分阶段验证

修改后需要验证：
- 现有数据源的采集-入库流程不受影响
- 新源（如未来新增的 baidu/sina 等）能直接存储，无需改白名单

## Risks / Trade-offs

- **"未实现爬虫"的源被意外存储** → 低风险。这些源没有爬虫产出数据，不会触发存储。即使手动调用存储 API 传入了这些源的数据，也是合法的（数据来源不限于爬虫）。
- **news_type 默认 "tech" 不准确** → 低风险。tech 是最通用分类。如果需要精确分类，后续可通过 LLM pipeline 覆盖。
