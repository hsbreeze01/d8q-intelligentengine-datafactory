# API 规格说明 - 虚拟组合模块

## 基础信息

- **Base URL**: http://47.99.57.152:8088
- **认证方式**: Session Cookie（username）
- **内容类型**: application/json

---

## 1. 组合 CRUD

### 1.1 获取组合列表

```
GET /api/portfolios
```

**响应 200**:
```json
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "name": "价值投资组合",
      "initial_capital": 1000000,
      "cash": 500000,
      "total_assets": 1150000,
      "return_rate": 0.15,
      "position_count": 5,
      "created_at": "2026-06-30T10:00:00"
    }
  ]
}
```

### 1.2 创建组合

```
POST /api/portfolios
```

**请求体**:
```json
{
  "name": "我的组合",
  "initial_capital": 1000000
}
```

**验证规则**:
- name: 必填，1-50 字符
- initial_capital: 必填，≥ 10000

**响应 201**:
```json
{
  "code": 0,
  "data": {
    "id": 1,
    "name": "我的组合",
    "initial_capital": 1000000,
    "cash": 1000000,
    "created_at": "2026-06-30T10:00:00"
  }
}
```

### 1.3 获取组合详情

```
GET /api/portfolios/{id}
```

**响应 200**:
```json
{
  "code": 0,
  "data": {
    "id": 1,
    "name": "价值投资组合",
    "initial_capital": 1000000,
    "cash": 500000,
    "total_assets": 1150000,
    "market_value": 650000,
    "profit": 150000,
    "return_rate": 0.15,
    "created_at": "2026-06-30T10:00:00",
    "positions": [
      {
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "quantity": 100,
        "avg_cost": 1800.00,
        "current_price": 1950.00,
        "market_value": 195000,
        "profit": 15000,
        "profit_rate": 0.0833
      }
    ]
  }
}
```

### 1.4 更新组合

```
PUT /api/portfolios/{id}
```

**请求体**:
```json
{
  "name": "新名称"
}
```

**响应 200**:
```json
{
  "code": 0,
  "message": "updated"
}
```

### 1.5 删除组合

```
DELETE /api/portfolios/{id}
```

**响应 200**:
```json
{
  "code": 0,
  "message": "deleted"
}
```

**说明**: 级联删除该组合下所有 positions、trades、net_value_history 记录。

---

## 2. 模拟交易

### 2.1 执行交易

```
POST /api/portfolios/{id}/trade
```

**请求体**:
```json
{
  "stock_code": "600519",
  "stock_name": "贵州茅台",
  "direction": "BUY",
  "price": 1800.00,
  "quantity": 100,
  "note": "看好白酒板块"
}
```

**验证规则**:
- stock_code: 必填，6位数字
- stock_name: 必填
- direction: 必填，枚举 BUY / SELL
- price: 必填，> 0
- quantity: 必填，正整数，买入需为100的整数倍
- note: 可选，≤ 200 字符

**BUY 额外校验**:
- price * quantity ≤ portfolio.cash

**SELL 额外校验**:
- 对应持仓 quantity ≥ 卖出 quantity

**响应 201**:
```json
{
  "code": 0,
  "data": {
    "trade_id": 1,
    "direction": "BUY",
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "price": 1800.00,
    "quantity": 100,
    "amount": 180000,
    "remaining_cash": 820000
  }
}
```

**错误响应 400**:
```json
{
  "code": 1,
  "message": "现金不足，当前可用: 50000.00，需要: 180000.00"
}
```

### 2.2 获取交易记录

```
GET /api/portfolios/{id}/trades?page=1&size=20
```

**响应 200**:
```json
{
  "code": 0,
  "data": {
    "total": 50,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": 1,
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "direction": "BUY",
        "price": 1800.00,
        "quantity": 100,
        "amount": 180000,
        "trade_date": "2026-06-30",
        "note": "看好白酒板块"
      }
    ]
  }
}
```

---

## 3. 绩效数据

### 3.1 获取绩效概览

```
GET /api/portfolios/{id}/performance
```

**响应 200**:
```json
{
  "code": 0,
  "data": {
    "summary": {
      "total_assets": 1150000,
      "market_value": 650000,
      "cash": 500000,
      "profit": 150000,
      "return_rate": 0.15,
      "max_drawdown": 0.08,
      "sharpe_ratio": 1.52,
      "win_rate": 0.65,
      "total_trades": 20
    },
    "net_value_series": [
      {"date": "2026-06-01", "net_value": 1.00},
      {"date": "2026-06-02", "net_value": 1.02},
      {"date": "2026-06-30", "net_value": 1.15}
    ],
    "benchmark_series": [
      {"date": "2026-06-01", "net_value": 1.00},
      {"date": "2026-06-02", "net_value": 1.01},
      {"date": "2026-06-30", "net_value": 1.08}
    ]
  }
}
```

### 3.2 刷新持仓现价（手动触发）

```
POST /api/portfolios/{id}/refresh-price
```

**响应 200**:
```json
{
  "code": 0,
  "data": {
    "updated_count": 5,
    "failed": ["688001"],
    "timestamp": "2026-06-30T15:30:00"
  }
}
```

---

## 4. 错误码定义

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 业务逻辑错误（现金不足/持仓不足等） |
| 2 | 参数校验失败 |
| 3 | 资源不存在 |
| 4 | 权限拒绝（非本人组合） |
| 5 | 服务端内部错误 |

---

## 5. 数据库 DDL

```sql
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    initial_capital REAL NOT NULL DEFAULT 1000000,
    cash REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost REAL NOT NULL DEFAULT 0,
    current_price REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, stock_code)
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('BUY', 'SELL')),
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    amount REAL NOT NULL,
    trade_date TEXT NOT NULL,
    note TEXT DEFAULT '',
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS net_value_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    net_value REAL NOT NULL,
    total_assets REAL NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, date)
);

CREATE INDEX idx_portfolios_user ON portfolios(user_id);
CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_trades_portfolio ON trades(portfolio_id);
CREATE INDEX idx_trades_date ON trades(trade_date);
CREATE INDEX idx_net_value_portfolio_date ON net_value_history(portfolio_id, date);
```
