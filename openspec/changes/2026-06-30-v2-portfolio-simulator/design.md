# 设计文档 - 虚拟组合模块

## 1. 架构概览

```
┌──────────────────────────────────────────────────────┐
│                   前端 SPA (D8Q)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐ │
│  │ 组合列表页  │  │ 组合详情页  │  │ ECharts看板    │ │
│  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘ │
└────────┼───────────────┼──────────────────┼──────────┘
         │               │                  │
         ▼               ▼                  ▼
┌──────────────────────────────────────────────────────┐
│              Factory (Flask, :8088)                    │
│  ┌──────────────────────────────────────────────┐    │
│  │  /api/portfolios      CRUD 组合               │    │
│  │  /api/portfolios/{id}/trade   模拟交易        │    │
│  │  /api/portfolios/{id}/performance  绩效数据   │    │
│  └──────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────┐    │
│  │  定时任务: 每日15:30刷新持仓现价              │    │
│  └──────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────┐    │
│  │  SQLite: portfolios / positions / trades      │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────┘
                        │ HTTP
                        ▼
┌──────────────────────────────────────────────────────┐
│         Shark (49.234.48.221:5000)                    │
│  GET /api/stock/quote?symbol=xxx → 实时价格           │
└──────────────────────────────────────────────────────┘
```

## 2. 数据模型

### 2.1 portfolios 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 组合ID |
| user_id | TEXT | NOT NULL | 用户名（来自session） |
| name | TEXT | NOT NULL | 组合名称 |
| initial_capital | REAL | NOT NULL, DEFAULT 1000000 | 初始资金（元） |
| cash | REAL | NOT NULL | 可用现金（初始=initial_capital） |
| created_at | TEXT | NOT NULL | 创建时间 ISO8601 |

### 2.2 positions 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 持仓ID |
| portfolio_id | INTEGER | FK → portfolios.id | 所属组合 |
| stock_code | TEXT | NOT NULL | 股票代码 如 600519 |
| stock_name | TEXT | NOT NULL | 股票名称 |
| quantity | INTEGER | NOT NULL | 持仓数量（股） |
| avg_cost | REAL | NOT NULL | 持仓成本价 |
| current_price | REAL | DEFAULT 0 | 最新价格 |
| updated_at | TEXT | NOT NULL | 最后更新时间 |

**唯一约束**: (portfolio_id, stock_code)

### 2.3 trades 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 交易ID |
| portfolio_id | INTEGER | FK → portfolios.id | 所属组合 |
| stock_code | TEXT | NOT NULL | 股票代码 |
| stock_name | TEXT | NOT NULL | 股票名称 |
| direction | TEXT | NOT NULL | BUY / SELL |
| price | REAL | NOT NULL | 成交价格 |
| quantity | INTEGER | NOT NULL | 成交数量 |
| amount | REAL | NOT NULL | 成交金额 = price * quantity |
| trade_date | TEXT | NOT NULL | 交易日期 |
| note | TEXT | DEFAULT '' | 备注 |

### 2.4 net_value_history 表（辅助）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| portfolio_id | INTEGER | FK → portfolios.id | |
| date | TEXT | NOT NULL | 日期 YYYY-MM-DD |
| net_value | REAL | NOT NULL | 当日净值 |
| total_assets | REAL | NOT NULL | 总资产 |

**唯一约束**: (portfolio_id, date)

## 3. 核心业务逻辑

### 3.1 买入逻辑

```python
def buy(portfolio, stock_code, stock_name, price, quantity):
    amount = price * quantity
    if portfolio.cash < amount:
        raise InsufficientFunds()
    
    portfolio.cash -= amount
    
    position = get_or_create_position(portfolio.id, stock_code)
    # 加权平均成本
    total_cost = position.avg_cost * position.quantity + amount
    position.quantity += quantity
    position.avg_cost = total_cost / position.quantity
    position.current_price = price
```

### 3.2 卖出逻辑

```python
def sell(portfolio, stock_code, price, quantity):
    position = get_position(portfolio.id, stock_code)
    if position.quantity < quantity:
        raise InsufficientShares()
    
    amount = price * quantity
    portfolio.cash += amount
    position.quantity -= quantity
    
    if position.quantity == 0:
        delete_position(position)
```

### 3.3 收益计算

```python
def calc_performance(portfolio):
    market_value = sum(p.quantity * p.current_price for p in portfolio.positions)
    total_assets = market_value + portfolio.cash
    profit = total_assets - portfolio.initial_capital
    return_rate = profit / portfolio.initial_capital
    return {
        'market_value': market_value,
        'cash': portfolio.cash,
        'total_assets': total_assets,
        'profit': profit,
        'return_rate': return_rate
    }
```

### 3.4 最大回撤

```python
def max_drawdown(net_values):
    peak = net_values[0]
    max_dd = 0
    for nv in net_values:
        peak = max(peak, nv)
        drawdown = (peak - nv) / peak
        max_dd = max(max_dd, drawdown)
    return max_dd
```

### 3.5 夏普比率

```python
def sharpe_ratio(daily_returns, risk_free_rate=0.03):
    import numpy as np
    excess = np.array(daily_returns) - risk_free_rate / 252
    if np.std(excess) == 0:
        return 0
    return np.mean(excess) / np.std(excess) * np.sqrt(252)
```

## 4. 定时任务设计

- **触发时间**: 每个交易日 15:30（收盘后）
- **实现方式**: APScheduler 或 threading.Timer
- **流程**:
  1. 查询所有 positions 表中出现的 stock_code（去重）
  2. 逐一调用 Shark `GET /api/stock/quote?symbol={code}`
  3. 批量更新 positions.current_price
  4. 计算每个 portfolio 的当日净值，写入 net_value_history
- **容错**: 单只股票查询失败不阻塞其他，记录错误日志

## 5. 前端设计

### 5.1 页面结构

```javascript
// PAGES 数组新增
{ id: 'portfolio', title: '虚拟组合', icon: '📊' }
```

### 5.2 组合列表视图

- 卡片式布局，每个组合显示：名称、总资产、收益率、创建日期
- 右上角「+新建组合」按钮
- 点击卡片进入组合详情

### 5.3 组合详情视图

- 顶部：组合摘要（总资产/现金/收益率/最大回撤/夏普比率）
- 中部Tab切换：
  - 持仓列表（表格：代码/名称/数量/成本/现价/盈亏/盈亏比例）
  - 交易记录（时间倒序）
  - 绩效看板（ECharts 净值曲线 + 沪深300叠加）
- 底部：快速交易表单（股票代码/方向/价格/数量）

### 5.4 ECharts 净值曲线

- X轴: 日期
- Y轴: 净值（初始=1.0）
- 双线叠加：组合净值 + 沪深300同期归一化净值
- tooltip 显示当日收益率差异

## 6. 安全设计

- 所有 API 校验 session 中的 username，仅操作自己的组合
- 卖出时检查持仓是否充足
- 买入时检查现金是否充足
- 防止负数交易量
- 组合名称长度限制 ≤ 50 字符
