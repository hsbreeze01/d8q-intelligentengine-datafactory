## ADDED Requirements

### R1: 推荐结果存储

**Given** 每日推荐引擎运行完毕
**When** 生成当日推荐列表
**Then** 自动将推荐记录写入 recommendation_results 表

- 字段包含: rec_date, stock_code, stock_name, rec_score, 4个维度分, price_at_rec(当日收盘价)
- T+N价格和收益率字段初始为 null，等待后续回填
- 每日推荐数量通常 5-10 只

### R2: T+N收益回填

**Given** 每个交易日收盘后(15:30触发)
**When** 执行 backfill_recommendation_returns 定时任务
**Then** 按天数差回填对应字段

- T+1: rec_date = today-1 的记录，回填 price_t1, return_t1
- T+3: rec_date = today-3 的记录，回填 price_t3, return_t3
- T+5: rec_date = today-5 的记录，回填 price_t5, return_t5, benchmark_t5
- T+10: rec_date = today-10 的记录，回填 price_t10, return_t10
- return_tN = (price_tN - price_at_rec) / price_at_rec * 100，保留2位小数
- 非交易日跳过（向后顺延到下一个交易日）
- benchmark_t5 = 沪深300同期涨跌幅

### R3: 历史推荐查询

**Given** 用户请求历史推荐数据
**When** GET /api/recommendation/history?days=30
**Then** 返回指定天数内的推荐记录列表

- 按 rec_date DESC 排序
- 支持分页: page, page_size(默认20)
- 每条记录包含 win 字段: return_t5 > 0 为 true，null为null
- 未回填的收益字段返回 null

### R4: 推荐统计

**Given** 用户请求统计数据
**When** GET /api/recommendation/stats?days=30
**Then** 返回胜率、平均收益、维度拆解、累计曲线

- win_rate_tN = count(return_tN > 0) / count(return_tN is not null) * 100
- avg_return_t5 = avg(return_t5) where return_t5 is not null
- excess_return_t5 = avg_return_t5 - avg(benchmark_t5)
- by_dimension: 对每个维度score排名前25%的子集计算独立胜率
- daily_cumulative_return: 每天推荐的T+5收益累加形成曲线

### R5: Factory代理

**Given** Factory接收前端请求
**When** 调用 /api/proxy/recommendation/history 或 /stats
**Then** 转发到 Shark 对应API并返回

- Factory使用现有 shark_request helper 转发
- 超时30s
- 错误时返回降级响应 {error: "..."}

### R6: 前端历史回溯Tab

**Given** 用户在推荐页点击「历史回溯」Tab
**When** Tab激活
**Then** 加载并渲染回溯数据

- 顶部统计卡: 4个指标(胜率T+5 / 超额收益 / 总推荐数 / 最佳单笔)
- ECharts折线图: X轴日期, Y轴累计收益率, 双线(推荐组合/沪深300)
- 维度胜率: 4个维度的胜率数字展示(或简单柱状图)
- 历史表格: 日期/股票/评分/T+1/T+3/T+5/T+10/胜负
  - 正收益: 绿色 +N.N%
  - 负收益: 红色 -N.N%
  - 未回填: 灰色 "--"
  - 胜: 绿色 ✓, 负: 红色 ✗

### R7: 数据积累与冷启动

**Given** 系统首次部署此功能
**When** 历史数据不足30天
**Then** 优雅降级

- 统计页显示"数据积累中，已有N天推荐记录"
- 曲线图仅展示已有数据点
- 补历史: 一次性脚本回溯填充过去30天数据(如Shark有历史推荐+日K数据)
