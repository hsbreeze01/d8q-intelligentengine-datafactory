# 设计文档 - 自选股日报与评分变化

## 架构概览

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  APScheduler │────▶│ score_calculator │────▶│ score_history   │
│  08:30 daily │     │ (遍历自选股)      │     │ (SQLite表)      │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                         │
                           ▼                         ▼
                    ┌──────────────┐          ┌──────────────────┐
                    │ comprehensive│          │ daily-report API │
                    │ API (已有)    │          │ score-history API│
                    └──────────────┘          └──────────────────┘
                                                     │
                                                     ▼
                                              ┌──────────────────┐
                                              │ 前端增强视图       │
                                              │ Table+Sparkline  │
                                              │ +归因弹窗         │
                                              └──────────────────┘
```

## 数据模型

### 新增表：score_history

```sql
CREATE TABLE IF NOT EXISTS score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    date TEXT NOT NULL,              -- YYYY-MM-DD
    total_score REAL NOT NULL,       -- 综合评分 0-100
    technical_score REAL,            -- 技术面评分
    trend_score REAL,                -- 趋势评分
    fundamental_score REAL,          -- 基本面评分
    volume_score REAL,               -- 量能评分
    signal TEXT,                     -- 信号: buy/sell/hold/strong_buy/strong_sell
    risk_level TEXT,                 -- 风险等级: low/medium/high
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, date)         -- 每只股票每天只有一条记录
);

CREATE INDEX idx_score_history_code_date ON score_history(stock_code, date DESC);
CREATE INDEX idx_score_history_date ON score_history(date);
```

### 与现有表关系

```
watchlist (已有)              score_history (新增)
├── user_id                  ├── stock_code ◄── watchlist.stock_code
├── stock_code ─────────────▶├── date
├── stock_name               ├── total_score
└── added_at                 ├── technical_score
                             ├── trend_score
                             ├── fundamental_score
                             ├── volume_score
                             ├── signal
                             └── risk_level
```

## 定时任务设计

### 调度策略

- **触发时间**：每个交易日 08:30（A股开盘前）
- **调度器**：APScheduler（Flask 应用内嵌）
- **幂等性**：UNIQUE(stock_code, date) 约束 + INSERT OR REPLACE 保证重跑安全

### 执行流程

```python
def daily_score_calculation():
    """每日评分计算定时任务"""
    today = date.today().strftime("%Y-%m-%d")
    
    # 1. 获取所有用户自选股（去重）
    stocks = get_all_watchlist_stocks_distinct()
    
    # 2. 逐只调用 comprehensive API
    for stock in stocks:
        result = call_comprehensive_api(stock.stock_code)
        
        # 3. 存入 score_history
        save_score_history(
            stock_code=stock.stock_code,
            date=today,
            total_score=result["score"],
            technical_score=result.get("technical_score"),
            trend_score=result.get("trend_score"),
            fundamental_score=result.get("fundamental_score"),
            volume_score=result.get("volume_score"),
            signal=derive_signal(result),
            risk_level=result["risk_level"]
        )
    
    logger.info(f"Daily score calculation completed: {len(stocks)} stocks")
```

### 容错处理

- 单只股票计算失败不影响其他股票
- 失败记录写入日志，不写入 score_history
- 支持手动触发补算：`POST /api/watchlist/recalculate?date=2026-06-30`

## API 设计

### GET /api/watchlist/daily-report

返回当前用户自选股的日报数据，包含今日评分、昨日评分、变化值。

**Response:**
```json
{
  "date": "2026-06-30",
  "stocks": [
    {
      "stock_code": "601318",
      "stock_name": "中国平安",
      "today_score": 72.5,
      "yesterday_score": 68.0,
      "change": 4.5,
      "change_pct": 6.6,
      "signal": "buy",
      "risk_level": "medium",
      "dimensions": {
        "technical": { "today": 75, "yesterday": 70, "change": 5 },
        "trend": { "today": 80, "yesterday": 78, "change": 2 },
        "fundamental": { "today": 65, "yesterday": 65, "change": 0 },
        "volume": { "today": 70, "yesterday": 59, "change": 11 }
      }
    }
  ],
  "summary": {
    "total_stocks": 8,
    "improved": 5,
    "declined": 2,
    "unchanged": 1,
    "avg_score": 68.3
  }
}
```

**排序规则**：默认按 `|change|` 降序（评分变化绝对值最大的排前面）。

### GET /api/watchlist/{code}/score-history?days=7

返回指定股票的历史评分数据，用于 sparkline 渲染。

**Response:**
```json
{
  "stock_code": "601318",
  "stock_name": "中国平安",
  "history": [
    {
      "date": "2026-06-24",
      "total_score": 65.0,
      "technical_score": 68,
      "trend_score": 72,
      "fundamental_score": 60,
      "volume_score": 55,
      "signal": "hold",
      "risk_level": "medium"
    },
    // ... 7天数据
  ]
}
```

## 前端设计

### 自选股列表改造

从简单 grid 升级为增强 table：

```
┌─────────────────────────────────────────────────────────────────┐
│ 自选股日报                                    2026-06-30 │
├──────┬──────┬─────┬─────┬──────┬────────┬───────┬──────────────┤
│ 代码  │ 名称  │今日分│昨日分│ 变化  │  信号   │ 风险  │  7日走势     │
├──────┼──────┼─────┼─────┼──────┼────────┼───────┼──────────────┤
│601318│中国平安│ 72.5│ 68.0│ +4.5▲│  买入  │  中   │ ╱─╲╱─╱▁    │
│000001│平安银行│ 58.0│ 65.0│ -7.0▼│  卖出  │  高   │ ╲──╱╲▁     │
│600519│贵州茅台│ 81.0│ 80.5│ +0.5─│  持有  │  低   │ ───────▁    │
└──────┴──────┴─────┴─────┴──────┴────────┴───────┴──────────────┘
```

### Sparkline 实现方案

采用 ECharts mini chart 方案：

```javascript
function renderSparkline(container, data) {
    const chart = echarts.init(container, null, { 
        width: 120, height: 30 
    });
    chart.setOption({
        grid: { top: 2, bottom: 2, left: 2, right: 2 },
        xAxis: { show: false, data: data.map(d => d.date) },
        yAxis: { show: false, min: "dataMin", max: "dataMax" },
        series: [{
            type: "line",
            smooth: true,
            symbol: "none",
            lineStyle: { width: 1.5 },
            areaStyle: { opacity: 0.1 },
            data: data.map(d => d.total_score)
        }]
    });
}
```

### 归因弹窗

点击某只股票行展开归因详情：

```
┌─────────────────────────────────────┐
│ 601318 中国平安 评分变化归因          │
├─────────────────────────────────────┤
│                                     │
│  技术面  ████████░░  70→75  (+5)    │
│  趋势    █████████░  78→80  (+2)    │
│  基本面  ██████░░░░  65→65  ( 0)    │
│  量能    ███████░░░  59→70  (+11) ★ │
│                                     │
│  ★ 主要变化维度：量能 (+11)          │
│  解读：成交量显著放大，多头力量增强    │
│                                     │
└─────────────────────────────────────┘
```

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 调度器 | APScheduler | Flask 生态内嵌，轻量，已有类似用法 |
| 存储 | SQLite score_history 表 | 与现有 financial_news.db 统一 |
| 前端图表 | ECharts (mini chart) | 页面已引入 ECharts，复用 |
| 前端框架 | 原生 JS + DOM | 与现有 SPA 保持一致 |

## 性能考量

- 30只自选股 × comprehensive API（约1s/只）= 30s 总计算时间
- 定时任务在 08:30 执行，不影响用户交互
- daily-report API 仅查 SQLite，响应 < 100ms
- Sparkline 数据量小（7×5 float），无需缓存
- 后续优化：可并发调用 comprehensive API 缩短计算时间
