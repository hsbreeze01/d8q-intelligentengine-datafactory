## Why

平台上线后，运营者无法知道用户实际如何使用系统 —— 哪些功能高频使用、哪些从没被碰过、用户停留多久、什么时候流失。当前没有任何行为数据采集能力，产品改进全凭直觉。需要建立"采集→分析→改进"的数据飞轮，让运营决策有据可依。

## What Changes

- **新增用户行为事件采集**：在 Factory 代理层通过中间件自动记录所有 API 调用事件（谁、什么时候、调了什么接口、响应时间），前端零埋点
- **新增事件存储**：Agent SQLite 新建 `user_events` 表，存储原始行为事件
- **新增聚合分析 API**：按用户/功能/时间段统计使用频次、活跃天数、功能偏好排名
- **新增运营分析看板**：Factory 设置页新增"运营分析"子 Tab，展示功能使用排行、用户活跃度趋势、功能冷热图、DAU/MAU
- **数据自动清理**：事件数据按天聚合归档，原始事件保留 90 天自动清理

## Capabilities

### New Capabilities
- `behavior-tracking`: 用户行为事件自动采集（Factory 中间件埋点 + Agent 存储）
- `analytics-dashboard`: 运营分析看板（功能排行、活跃趋势、冷热图、用户画像）

### Modified Capabilities
<!-- 无现有 spec 需修改 -->

## Impact

- **Factory `app.py`**：新增 `@app.after_request` 中间件，自动记录 API 事件
- **Agent `user_routes.py`**：新增 `user_events` 表创建 + 事件写入 + 聚合查询端点
- **Factory `templates/index.html`**：设置页新增"运营分析"子 Tab，ECharts 可视化
- **数据存储**：Agent SQLite `user_events` 表，预估 10 用户 × 日均 200 次 = 日增 2000 行，90 天约 18 万行，可接受
- **性能影响**：事件写入为异步 INSERT，对 API 响应时间影响 < 5ms
