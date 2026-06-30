# 设计文档：投融资数据增强(热力图+机构追踪)

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (D8Q)                         │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │事件列表Tab│  │热力分析Tab    │  │机构追踪Tab        │  │
│  │(现有)     │  │Heatmap+Line  │  │Ranking+Follow    │  │
│  │          │  │+Pie (ECharts)│  │+Detail           │  │
│  └──────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────────┐
│              Factory (Node.js/Express)                    │
│  /api/investment/heatmap    → proxy to Agent             │
│  /api/investment/investors/top → proxy to Agent          │
│  /api/investment/follow     → followed_investors CRUD    │
│  /api/investment/follow/check-alerts → 预警联动          │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────────┐
│              Agent (Python/FastAPI :8000)                 │
│  GET /api/itjuzi/heatmap?months=6                        │
│  GET /api/itjuzi/investors/top?days=90&limit=20          │
│  (基于 itjuzi_investevent 表聚合查询)                     │
└─────────────────────────────────────────────────────────┘
```

## 数据模型

### 现有表：itjuzi_investevent
```sql
-- 关键字段（已有）
id, source, event_date, company_name, company_brief,
industry, sub_industries(JSON), round, amount_text,
amount_cny_est, currency, investors(JSON [{name,is_lead}]), source_url
```

### 新增表：followed_investors (Factory端)
```sql
CREATE TABLE followed_investors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL COMMENT 用户ID,
    investor_name VARCHAR(200) NOT NULL COMMENT 机构名称,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_investor (user_id, investor_name),
    KEY idx_investor_name (investor_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT=用户关注的投资机构;
```

## API设计

### Agent端新增API

#### 1. GET /api/itjuzi/heatmap

热力图数据：按月×行业聚合事件数和融资金额。

**参数：**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| months | int | 6 | 回溯月数(1-24) |
| metric | string | "count" | 聚合指标: count/amount |

**响应：**
```json
{
  "months": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
  "industries": ["企业服务", "医疗健康", "人工智能", "金融", "电商零售"],
  "matrix": [
    [12, 8, 15, 6, 9, 11],
    [7, 5, 9, 12, 8, 6],
    ...
  ],
  "trend": {
    "months": ["2026-01", ...],
    "event_count": [45, 38, 52, 41, 49, 55],
    "total_amount": [128.5, 95.2, 156.8, 112.3, 143.7, 168.9]
  },
  "round_distribution": [
    {"round": "天使轮", "count": 35, "amount": 12.5},
    {"round": "Pre-A轮", "count": 28, "amount": 45.2},
    {"round": "A轮", "count": 42, "amount": 89.6},
    {"round": "B轮", "count": 25, "amount": 156.3},
    {"round": "C轮", "count": 15, "amount": 234.8},
    {"round": "D轮及以上", "count": 8, "amount": 312.5},
    {"round": "战略融资", "count": 18, "amount": 78.4}
  ]
}
```

**实现逻辑：**
```sql
-- 热力图矩阵
SELECT DATE_FORMAT(event_date, %Y-%m) as month,
       industry,
       COUNT(*) as event_count,
       SUM(COALESCE(amount_cny_est, 0)) as total_amount
FROM itjuzi_investevent
WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL :months MONTH)
GROUP BY month, industry
ORDER BY month, event_count DESC;

-- 趋势数据
SELECT DATE_FORMAT(event_date, %Y-%m) as month,
       COUNT(*) as event_count,
       SUM(COALESCE(amount_cny_est, 0)) as total_amount
FROM itjuzi_investevent
WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL :months MONTH)
GROUP BY month ORDER BY month;

-- 轮次分布
SELECT round, COUNT(*) as count,
       SUM(COALESCE(amount_cny_est, 0)) as amount
FROM itjuzi_investevent
WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL :months MONTH)
GROUP BY round ORDER BY count DESC;
```

#### 2. GET /api/itjuzi/investors/top

活跃机构排行榜。

**参数：**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| days | int | 90 | 回溯天数 |
| limit | int | 20 | 返回数量 |
| industry | string | - | 按行业筛选(可选) |

**响应：**
```json
[
  {
    "name": "红杉中国",
    "deal_count": 12,
    "lead_count": 5,
    "total_amount": 45.8,
    "industries": ["人工智能", "企业服务", "医疗健康"],
    "recent_deals": [
      {"company": "XX科技", "round": "B轮", "date": "2026-06-28", "amount": "2亿人民币"},
      {"company": "YY生物", "round": "A轮", "date": "2026-06-25", "amount": "5000万人民币"}
    ]
  }
]
```

**实现逻辑：**
```python
# 从investors JSON中提取机构名，聚合统计
# 1. 查询时间范围内所有事件
# 2. 解析每条事件的investors JSON
# 3. 按机构名聚合: deal_count, lead_count, total_amount
# 4. 排序取Top N
# 5. 补充recent_deals明细

SELECT id, event_date, company_name, round, amount_text,
       amount_cny_est, industry, investors
FROM itjuzi_investevent
WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
  AND investors IS NOT NULL AND investors != [];
```

### Factory端新增API

#### 3. GET /api/investment/heatmap
代理到Agent GET /api/itjuzi/heatmap，透传参数。

#### 4. GET /api/investment/investors/top
代理到Agent GET /api/itjuzi/investors/top，透传参数。

#### 5. POST /api/investment/follow
关注机构。

**请求体：**
```json
{ "investor_name": "红杉中国" }
```

#### 6. DELETE /api/investment/follow/:investor_name
取消关注。

#### 7. GET /api/investment/follow
获取当前用户关注的机构列表。

**响应：**
```json
{
  "followed": ["红杉中国", "IDG资本", "高瓴创投"]
}
```

#### 8. POST /api/investment/follow/check-alerts (内部定时调用)
检查关注机构的新投资事件，生成预警。

**逻辑：**
1. 查询所有被关注的机构名(去重)
2. 调用Agent查询这些机构最近24h内的新投资事件
3. 匹配关注了该机构的用户
4. 向alerts表写入预警记录
5. 通过WebSocket推送给在线用户

## 前端设计

### Tab结构改造

```javascript
// loadInvestment 改造
function loadInvestment() {
  const container = document.getElementById(investment-content);
  container.innerHTML = `
    <div class="tab-nav">
      <button class="tab-btn active" data-tab="events">事件列表</button>
      <button class="tab-btn" data-tab="heatmap">热力分析</button>
      <button class="tab-btn" data-tab="investors">机构追踪</button>
    </div>
    <div class="tab-content" id="investment-tab-content"></div>
  `;
  loadEventsTab(); // 默认加载事件列表
}
```

### 热力分析Tab

- **热力图(ECharts heatmap)**：X轴=月份，Y轴=行业，色值=事件数/金额
- **趋势折线图**：双Y轴，左=事件数，右=融资金额(亿元)
- **轮次饼图**：按轮次分布，hover显示占比和金额

### 机构追踪Tab

- **排行榜表格**：序号、机构名、出手次数、领投次数、总金额、关注按钮
- **关注按钮**：已关注=实心星/取消关注，未关注=空心星/点击关注
- **展开详情**：点击机构行展开recent_deals列表
- **筛选**：支持按天数(30/60/90/180)和行业筛选

## 预警联动设计

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Cron Job    │────▶│ check-alerts │────▶│ alerts表    │
│ 每小时执行  │     │ API          │     │ + WebSocket │
└─────────────┘     └──────────────┘     └─────────────┘
```

预警记录格式：
```json
{
  "type": "investment_follow",
  "title": "关注机构新投资",
  "content": "红杉中国 领投 XX科技 B轮 2亿人民币",
  "metadata": {
    "investor_name": "红杉中国",
    "company_name": "XX科技",
    "round": "B轮",
    "amount": "2亿人民币",
    "event_date": "2026-06-28"
  }
}
```

## 性能考虑

1. **热力图缓存**：Agent端对heatmap结果做5分钟Redis缓存，避免大量聚合查询
2. **机构排行缓存**：investors/top结果缓存10分钟
3. **前端懒加载**：Tab切换时才请求对应数据
4. **分页**：机构排行默认Top20，支持loadMore

## 安全考虑

1. Factory代理层做用户鉴权，follow操作绑定当前登录用户
2. Agent端API保持内网访问，不对外暴露
3. investor_name做SQL注入防护（参数化查询）
