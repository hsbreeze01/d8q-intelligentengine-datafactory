# 技术规格 - 自选股日报与评分变化

## 1. 数据库变更

### 1.1 新增表 score_history

**文件**：`financial_news.db`

```sql
CREATE TABLE IF NOT EXISTS score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    date TEXT NOT NULL,
    total_score REAL NOT NULL,
    technical_score REAL DEFAULT 0,
    trend_score REAL DEFAULT 0,
    fundamental_score REAL DEFAULT 0,
    volume_score REAL DEFAULT 0,
    signal TEXT DEFAULT 'hold',
    risk_level TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, date)
);

CREATE INDEX IF NOT EXISTS idx_score_history_code_date 
    ON score_history(stock_code, date DESC);
CREATE INDEX IF NOT EXISTS idx_score_history_date 
    ON score_history(date);
```

### 1.2 字段说明

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| stock_code | TEXT | NOT NULL | 股票代码，如 601318 |
| date | TEXT | NOT NULL | 日期 YYYY-MM-DD |
| total_score | REAL | NOT NULL | 综合评分 0-100 |
| technical_score | REAL | DEFAULT 0 | 技术面评分 0-100 |
| trend_score | REAL | DEFAULT 0 | 趋势评分 0-100 |
| fundamental_score | REAL | DEFAULT 0 | 基本面评分 0-100 |
| volume_score | REAL | DEFAULT 0 | 量能评分 0-100 |
| signal | TEXT | DEFAULT hold | 信号: strong_buy/buy/hold/sell/strong_sell |
| risk_level | TEXT | DEFAULT medium | 风险: low/medium/high |
| created_at | TIMESTAMP | DEFAULT NOW | 记录创建时间 |

### 1.3 约束

- `UNIQUE(stock_code, date)`：每只股票每天最多一条记录
- 使用 `INSERT OR REPLACE` 实现幂等写入

---

## 2. 后端 API 规格

### 2.1 GET /api/watchlist/daily-report

**描述**：获取当前用户自选股日报，含今日/昨日评分及变化。

**请求参数**：

| 参数 | 位置 | 类型 | 必选 | 说明 |
|------|------|------|------|------|
| date | query | string | 否 | 指定日期，默认今天，格式 YYYY-MM-DD |
| sort | query | string | 否 | 排序方式，默认 change_desc |

**sort 可选值**：
- `change_desc`：按评分变化绝对值降序（默认）
- `score_desc`：按今日评分降序
- `score_asc`：按今日评分升序
- `name_asc`：按名称升序

**响应 200**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": "2026-06-30",
    "generated_at": "2026-06-30T08:30:15",
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
          "technical": { "today": 75.0, "yesterday": 70.0, "change": 5.0 },
          "trend": { "today": 80.0, "yesterday": 78.0, "change": 2.0 },
          "fundamental": { "today": 65.0, "yesterday": 65.0, "change": 0.0 },
          "volume": { "today": 70.0, "yesterday": 59.0, "change": 11.0 }
        },
        "sparkline": [65.0, 66.5, 67.0, 68.0, 70.0, 68.0, 72.5]
      }
    ],
    "summary": {
      "total_stocks": 8,
      "improved": 5,
      "declined": 2,
      "unchanged": 1,
      "avg_score": 68.3,
      "max_change_stock": "000001",
      "max_change_value": -7.0
    }
  }
}
```

**响应 404**：无自选股数据
```json
{
  "code": 404,
  "message": "No watchlist found",
  "data": null
}
```

**逻辑**：
1. 从 watchlist 表获取当前用户（默认 user_id=1）的自选股
2. 从 score_history 获取 date 和 date-1 的评分
3. 计算 change = today - yesterday
4. 取最近7天数据填充 sparkline 数组
5. 按 sort 参数排序后返回

---

### 2.2 GET /api/watchlist/{code}/score-history

**描述**：获取指定股票的历史评分数据。

**请求参数**：

| 参数 | 位置 | 类型 | 必选 | 说明 |
|------|------|------|------|------|
| code | path | string | 是 | 股票代码 |
| days | query | int | 否 | 天数，默认 7，最大 90 |

**响应 200**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "stock_code": "601318",
    "stock_name": "中国平安",
    "days": 7,
    "history": [
      {
        "date": "2026-06-24",
        "total_score": 65.0,
        "technical_score": 68.0,
        "trend_score": 72.0,
        "fundamental_score": 60.0,
        "volume_score": 55.0,
        "signal": "hold",
        "risk_level": "medium"
      }
    ],
    "trend": {
      "direction": "up",
      "avg_score": 68.2,
      "min_score": 65.0,
      "max_score": 72.5,
      "volatility": 2.8
    }
  }
}
```

**响应 404**：股票不在自选股中或无历史数据
```json
{
  "code": 404,
  "message": "No score history found for {code}",
  "data": null
}
```

---

### 2.3 POST /api/watchlist/recalculate

**描述**：手动触发评分重新计算（管理/调试用）。

**请求体**：
```json
{
  "date": "2026-06-30",
  "stock_codes": ["601318", "000001"]  // 可选，为空则计算全部
}
```

**响应 200**：
```json
{
  "code": 0,
  "message": "Recalculation started",
  "data": {
    "stocks_count": 2,
    "date": "2026-06-30"
  }
}
```

---

## 3. 定时任务规格

### 3.1 调度配置

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=daily_score_calculation,
    trigger=CronTrigger(hour=8, minute=30),
    id="watchlist_daily_score",
    name="自选股每日评分计算",
    replace_existing=True,
    misfire_grace_time=3600  # 1小时内可补执行
)
```

### 3.2 执行逻辑

```python
def daily_score_calculation(target_date=None):
    """
    每日评分计算主函数
    
    Args:
        target_date: 指定日期(YYYY-MM-DD)，默认今天
    """
    calc_date = target_date or date.today().strftime("%Y-%m-%d")
    
    # 获取所有自选股（去重）
    db = get_db()
    stocks = db.execute(
        "SELECT DISTINCT stock_code, stock_name FROM watchlist"
    ).fetchall()
    
    success_count = 0
    fail_count = 0
    
    for stock in stocks:
        try:
            # 调用 comprehensive API
            result = requests.post(
                "http://127.0.0.1:8088/api/stock/comprehensive",
                json={"stock_code": stock["stock_code"]},
                timeout=30
            ).json()
            
            # 写入 score_history
            db.execute("""
                INSERT OR REPLACE INTO score_history 
                (stock_code, date, total_score, technical_score, 
                 trend_score, fundamental_score, volume_score, 
                 signal, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stock["stock_code"],
                calc_date,
                result.get("score", 0),
                result.get("technical_score", 0),
                result.get("trend_score", 0),
                result.get("fundamental_score", 0),
                result.get("volume_score", 0),
                derive_signal(result),
                result.get("risk_level", "medium")
            ))
            success_count += 1
        except Exception as e:
            logger.error(f"Score calc failed for {stock[stock_code]}: {e}")
            fail_count += 1
    
    db.commit()
    logger.info(
        f"Daily score calc done: date={calc_date}, "
        f"success={success_count}, failed={fail_count}"
    )
```

### 3.3 信号派生逻辑

```python
def derive_signal(result):
    """根据综合分析结果派生交易信号"""
    score = result.get("score", 50)
    short_term = result.get("short_term", "neutral")
    
    if score >= 80 and short_term == "bullish":
        return "strong_buy"
    elif score >= 65 and short_term in ("bullish", "neutral"):
        return "buy"
    elif score <= 30 and short_term == "bearish":
        return "strong_sell"
    elif score <= 45 and short_term in ("bearish", "neutral"):
        return "sell"
    else:
        return "hold"
```

---

## 4. 前端规格

### 4.1 HTML 结构变更

**位置**：`templates/index.html` 中自选股区域

```html
<div id="watchlist-daily-report" class="watchlist-enhanced">
    <div class="report-header">
        <h3>自选股日报</h3>
        <span class="report-date" id="report-date"></span>
        <div class="report-summary" id="report-summary"></div>
    </div>
    <table class="watchlist-table" id="watchlist-table">
        <thead>
            <tr>
                <th>代码</th>
                <th>名称</th>
                <th>今日分</th>
                <th>昨日分</th>
                <th class="sortable active">变化</th>
                <th>信号</th>
                <th>风险</th>
                <th>7日走势</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody id="watchlist-tbody"></tbody>
    </table>
    <!-- 归因弹窗 -->
    <div id="attribution-modal" class="modal hidden">
        <div class="modal-content">
            <div class="modal-header">
                <span id="attr-stock-name"></span>
                <button class="modal-close">&times;</button>
            </div>
            <div id="attr-dimensions" class="dimensions-chart"></div>
        </div>
    </div>
</div>
```

### 4.2 JavaScript 接口

```javascript
// 加载日报数据
async function loadDailyReport(sort = "change_desc") {
    const resp = await fetch(`/api/watchlist/daily-report?sort=${sort}`);
    const { data } = await resp.json();
    renderDailyReport(data);
}

// 渲染日报表格
function renderDailyReport(report) {
    const tbody = document.getElementById("watchlist-tbody");
    tbody.innerHTML = "";
    
    report.stocks.forEach(stock => {
        const row = document.createElement("tr");
        row.className = getChangeClass(stock.change);
        row.onclick = () => showAttribution(stock);
        
        row.innerHTML = `
            <td>${stock.stock_code}</td>
            <td>${stock.stock_name}</td>
            <td class="score">${stock.today_score.toFixed(1)}</td>
            <td class="score-dim">${stock.yesterday_score.toFixed(1)}</td>
            <td class="change ${stock.change > 0 ? 'up' : stock.change < 0 ? 'down' : 'flat'}">${formatChange(stock.change)}</td>
            <td class="signal signal-${stock.signal}">${SIGNAL_LABELS[stock.signal]}</td>
            <td class="risk risk-${stock.risk_level}">${RISK_LABELS[stock.risk_level]}</td>
            <td class="sparkline" id="spark-${stock.stock_code}"></td>
            <td><button onclick="event.stopPropagation(); removeWatchlist('${stock.stock_code}')">&times;</button></td>
        `;
        tbody.appendChild(row);
        
        // 渲染 sparkline
        if (stock.sparkline && stock.sparkline.length > 0) {
            renderSparkline(
                document.getElementById(`spark-${stock.stock_code}`),
                stock.sparkline,
                stock.change >= 0
            );
        }
    });
    
    // 渲染摘要
    renderSummary(report.summary);
}

// Sparkline 渲染
function renderSparkline(container, scores, isUp) {
    const chart = echarts.init(container, null, { width: 120, height: 30 });
    chart.setOption({
        grid: { top: 2, bottom: 2, left: 2, right: 2 },
        xAxis: { show: false, type: "category" },
        yAxis: { show: false, type: "value", min: "dataMin", max: "dataMax" },
        series: [{
            type: "line",
            smooth: true,
            symbol: "none",
            lineStyle: { width: 1.5, color: isUp ? "#e74c3c" : "#27ae60" },
            areaStyle: { 
                opacity: 0.1, 
                color: isUp ? "#e74c3c" : "#27ae60" 
            },
            data: scores
        }]
    });
}

// 归因弹窗
function showAttribution(stock) {
    const modal = document.getElementById("attribution-modal");
    document.getElementById("attr-stock-name").textContent = 
        `${stock.stock_code} ${stock.stock_name} 评分变化归因`;
    
    renderAttributionChart(stock.dimensions);
    modal.classList.remove("hidden");
}

// 归因柱状图
function renderAttributionChart(dimensions) {
    const container = document.getElementById("attr-dimensions");
    const chart = echarts.init(container, null, { height: 250 });
    
    const dims = [
        { name: "技术面", key: "technical" },
        { name: "趋势", key: "trend" },
        { name: "基本面", key: "fundamental" },
        { name: "量能", key: "volume" }
    ];
    
    chart.setOption({
        tooltip: { trigger: "axis" },
        xAxis: { type: "category", data: dims.map(d => d.name) },
        yAxis: { type: "value" },
        series: [
            {
                name: "昨日",
                type: "bar",
                data: dims.map(d => dimensions[d.key].yesterday),
                itemStyle: { color: "#bdc3c7" }
            },
            {
                name: "今日",
                type: "bar",
                data: dims.map(d => dimensions[d.key].today),
                itemStyle: { color: "#3498db" }
            },
            {
                name: "变化",
                type: "bar",
                data: dims.map(d => dimensions[d.key].change),
                itemStyle: { 
                    color: (params) => params.value >= 0 ? "#e74c3c" : "#27ae60"
                }
            }
        ]
    });
}
```

### 4.3 CSS 样式要点

```css
.watchlist-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.watchlist-table th { background: #f8f9fa; padding: 8px 12px; text-align: left; }
.watchlist-table td { padding: 8px 12px; border-bottom: 1px solid #eee; }
.watchlist-table tr:hover { background: #f0f7ff; cursor: pointer; }

.change.up { color: #e74c3c; font-weight: bold; }
.change.down { color: #27ae60; font-weight: bold; }
.change.flat { color: #95a5a6; }

.signal-strong_buy { background: #e74c3c; color: white; }
.signal-buy { background: #ff7675; color: white; }
.signal-hold { background: #fdcb6e; color: #333; }
.signal-sell { background: #55a3e8; color: white; }
.signal-strong_sell { background: #2d3436; color: white; }

.risk-low { color: #27ae60; }
.risk-medium { color: #f39c12; }
.risk-high { color: #e74c3c; }
```

---

## 5. 信号与颜色映射

| signal | 中文 | 颜色 | 含义 |
|--------|------|------|------|
| strong_buy | 强烈买入 | #e74c3c 红底白字 | 评分≥80 且短期看涨 |
| buy | 买入 | #ff7675 浅红底白字 | 评分≥65 且非看跌 |
| hold | 持有 | #fdcb6e 黄底黑字 | 中性区间 |
| sell | 卖出 | #55a3e8 蓝底白字 | 评分≤45 且非看涨 |
| strong_sell | 强烈卖出 | #2d3436 深色底白字 | 评分≤30 且短期看跌 |

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|---------|
| comprehensive API 超时 | 跳过该股票，记录日志，不写入 score_history |
| 无昨日评分数据 | yesterday_score=null, change=null, 前端显示 "--" |
| 无7日历史 | sparkline 显示已有天数，不足7天按实际显示 |
| 自选股为空 | 返回空 stocks 数组，前端显示引导提示 |
| SQLite 写入冲突 | INSERT OR REPLACE 覆盖 |
