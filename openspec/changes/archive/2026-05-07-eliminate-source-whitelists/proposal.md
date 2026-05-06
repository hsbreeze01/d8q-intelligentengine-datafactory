## Why

新增数据源时需要在 6 个独立位置手动注册（枚举、ACTIVE_SOURCES、CRAWL_MAP、两个存储白名单、赛道默认源）。漏配存储白名单时数据被静默丢弃，API 返回的 total_count 与实际入库数不一致。量子计算赛道踩坑即因此而起。

## What Changes

- 删除 `financial_news_storage_tools.py` 中的 `financial_sources` 硬编码白名单，改为基于 DataSource 枚举验证
- 删除 `financial_news_storage.py` 中的 `financial_platforms` 硬编码白名单，改为基于 DataSource 枚举验证
- 确保 `enhanced_financial_news_storage.py` 的 INSERT 语句包含 `news_type` 字段，默认值为 `"tech"`
- 验证所有现有源在白名单移除后仍能正常入库

## Capabilities

### New Capabilities
- `source-storage-parity`: 数据源存储层与枚举层一致性保证——任何通过 DataSource 枚举注册的源均可存储

### Modified Capabilities

## Impact

- **Data-agent** `tools/financial_news_storage_tools.py`: 删除硬编码白名单，改为枚举验证
- **Data-agent** `storage/financial_news_storage.py`: 删除硬编码白名单，改为枚举验证
- **Data-agent** `storage/enhanced_financial_news_storage.py`: INSERT 增加 news_type 默认值
- **新增源时步骤从 6 步降为 2 步**（枚举 + crawl 函数）
- **无数据库 schema 变更**（news_type 列已存在）
- **无前端变更**
