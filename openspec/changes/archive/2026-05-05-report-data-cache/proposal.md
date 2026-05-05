## Why

研报搜索每次请求都直接调用 StockShark 远端 API，不同用户搜索相同股票会触发重复远端请求。研报和公告属于公共数据，时效性要求不高（分钟级延迟可接受），适合在 Factory 层做缓存，减少远端调用、降低延迟、提升体验。

## What Changes

- 在 Factory（:8088）层新增研报数据缓存，以 `(keyword, type)` 为 key 缓存远端 API 返回结果
- 研报缓存 TTL 30 分钟，公告缓存 TTL 15 分钟（公告更新频率略高）
- 缓存不区分用户 — 研报数据为公共数据，任何用户搜索相同关键词命中同一份缓存
- 用户级过滤在前端完成（搜索关键词、结果展示范围），后端只负责数据获取和缓存
- 批量搜索时，对缓存命中的关键词跳过远端调用，仅请求未命中部分
- 缓存命中/未命中统计通过响应 header 返回，便于监控

## Capabilities

### New Capabilities
- `report-cache`: Factory 层研报与公告数据内存缓存，以关键词为维度存储，TTL 过期自动失效，批量查询时自动拆分命中/未命中批次

### Modified Capabilities

## Impact

- **Factory app.py**: `report_stock_query()` 和 `/api/report/search` 路由需改写为先查缓存、未命中再调远端
- **无数据库变更**: 使用内存字典缓存（单 worker 场景足够），无需 Redis/DB
- **API 契约不变**: `/api/report/stock` 和 `/api/report/search` 请求/响应格式不变，前端无需改动
- **StockShark**: 无改动
