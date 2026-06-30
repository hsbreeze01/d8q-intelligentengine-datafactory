# Design: 推荐回溯验证

## Architecture

```
Shark (49.234.48.221:5000)
  |-- 每日推荐引擎 --> recommendation_daily 表 (已有)
  |-- 新增: recommendation_results 表 (回填T+N收益)
  |-- 新增: 每日定时任务 backfill_recommendation_returns
  |      (T+1当天回填, T+3第3天回填, T+5第5天, T+10第10天)
  |-- 新增API: GET /api/recommendation/history
  |-- 新增API: GET /api/recommendation/stats

Factory (47.99.57.152:8088)
  |-- 新增代理: GET /api/proxy/recommendation/history
  |-- 新增代理: GET /api/proxy/recommendation/stats
  |-- 前端: recommend页新增 "历史回溯" Tab
```

## Data Model (Shark端)

### recommendation_results 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| rec_date | DATE | 推荐日期 |
| stock_code | TEXT | 股票代码 |
| stock_name | TEXT | 股票名称 |
| rec_score | REAL | 推荐时综合评分 |
| technical_score | REAL | 技术面分 |
| trend_score | REAL | 趋势分 |
| fundamental_score | REAL | 基本面分 |
| volume_score | REAL | 量能分 |
| price_at_rec | REAL | 推荐时价格(当日收盘) |
| price_t1 | REAL | T+1收盘价 |
| price_t3 | REAL | T+3收盘价 |
| price_t5 | REAL | T+5收盘价 |
| price_t10 | REAL | T+10收盘价 |
| return_t1 | REAL | T+1收益率(%) |
| return_t3 | REAL | T+3收益率(%) |
| return_t5 | REAL | T+5收益率(%) |
| return_t10 | REAL | T+10收益率(%) |
| benchmark_t5 | REAL | 同期沪深300收益率(T+5) |
| filled_at | TIMESTAMP | 最后回填时间 |

索引: (rec_date DESC), (stock_code, rec_date)

## API Design (Shark端)

### GET /api/recommendation/history
- Params: days(默认30), page, page_size
- Response:
```
{
  "items": [
    {
      "rec_date": "2026-06-28",
      "stock_code": "002594",
      "stock_name": "比亚迪",
      "rec_score": 82,
      "price_at_rec": 285.50,
      "return_t1": 1.2,
      "return_t3": -0.5,
      "return_t5": 3.8,
      "return_t10": null,
      "benchmark_t5": 0.9,
      "win": true
    }
  ],
  "total": 150
}
```

### GET /api/recommendation/stats
- Params: days(默认30)
- Response:
```
{
  "total_recommendations": 150,
  "win_rate_t1": 55.3,
  "win_rate_t3": 52.0,
  "win_rate_t5": 58.7,
  "win_rate_t10": 61.2,
  "avg_return_t5": 2.1,
  "avg_benchmark_t5": 0.8,
  "excess_return_t5": 1.3,
  "by_dimension": {
    "high_technical": {"count": 40, "win_rate_t5": 65.0},
    "high_trend": {"count": 35, "win_rate_t5": 57.1},
    "high_fundamental": {"count": 30, "win_rate_t5": 53.3},
    "high_volume": {"count": 25, "win_rate_t5": 60.0}
  },
  "daily_cumulative_return": [
    {"date": "2026-06-01", "portfolio": 0.5, "benchmark": 0.2},
    {"date": "2026-06-02", "portfolio": 1.1, "benchmark": 0.3}
  ]
}
```

## Backfill Logic (Shark定时任务)

每日收盘后(15:30)执行:
1. 查询所有 price_t1=null 且 rec_date = today-1 的记录 → 回填T+1
2. 查询所有 price_t3=null 且 rec_date = today-3 的记录 → 回填T+3
3. 查询所有 price_t5=null 且 rec_date = today-5 的记录 → 回填T+5
4. 查询所有 price_t10=null 且 rec_date = today-10 的记录 → 回填T+10
5. 计算 return_tN = (price_tN - price_at_rec) / price_at_rec * 100
6. 获取同期沪深300涨跌幅作为benchmark_t5

价格来源: Shark本地的股票日K数据(已有)

## Frontend Design

### 推荐页改造
在现有 loadRecommend 基础上新增Tab:
- [每日荐股] (现有) | [行业板块] (现有) | [赛道热度] (现有) | [历史回溯] (新增)

### 历史回溯Tab内容
1. **顶部统计卡**: 胜率T+5 / 平均超额收益 / 推荐总数 / 最佳推荐
2. **累计收益曲线**: ECharts双线图(推荐组合 vs 沪深300)
3. **维度胜率雷达图**: 4个维度的胜率对比
4. **历史推荐表格**: 日期/股票/评分/T+1~T+10收益/胜负标记
   - 正收益绿色，负收益红色
   - 未回填数据显示"--"
   - 支持按日期范围筛选
