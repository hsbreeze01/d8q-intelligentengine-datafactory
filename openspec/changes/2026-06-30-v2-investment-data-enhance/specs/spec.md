# 技术规格：投融资数据增强(热力图+机构追踪)

## 1. Agent端 - 热力图API

### 1.1 GET /api/itjuzi/heatmap

**文件位置：** `agent/routers/itjuzi.py` (新增路由)

**请求参数：**
```
GET /api/itjuzi/heatmap?months=6&metric=count
```

| 参数 | 类型 | 必填 | 默认值 | 校验规则 |
|------|------|------|--------|----------|
| months | integer | 否 | 6 | 1 ≤ months ≤ 24 |
| metric | string | 否 | "count" | enum: count, amount |

**响应格式 (200 OK)：**
```json
{
  "code": 0,
  "data": {
    "months": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
    "industries": ["企业服务", "医疗健康", "人工智能", "金融", "电商零售"],
    "matrix": [[12, 8, 15, 6, 9, 11], [7, 5, 9, 12, 8, 6]],
    "trend": {
      "months": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
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
}
```

**字段说明：**
- `months`: 时间轴标签数组，格式YYYY-MM
- `industries`: 行业标签数组，按总事件数降序取Top10
- `matrix`: 二维数组，matrix[i][j] = industries[i]在months[j]的指标值
- `trend.event_count`: 每月总事件数
- `trend.total_amount`: 每月总融资金额(亿元人民币)
- `round_distribution[].amount`: 该轮次总融资金额(亿元人民币)

**SQL实现：**
```sql
-- 热力图矩阵数据
SELECT DATE_FORMAT(event_date, '%Y-%m') AS month,
       industry,
       COUNT(*) AS event_count,
       ROUND(SUM(COALESCE(amount_cny_est, 0)) / 100000000, 2) AS total_amount_yi
FROM itjuzi_investevent
WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL ? MONTH)
  AND industry IS NOT NULL AND industry != ''
GROUP BY month, industry
ORDER BY month ASC;

-- 行业排序(取Top10)
SELECT industry, COUNT(*) AS total
FROM itjuzi_investevent
WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL ? MONTH)
  AND industry IS NOT NULL AND industry != ''
GROUP BY industry
ORDER BY total DESC
LIMIT 10;
```

**缓存策略：**
- Key: `itjuzi:heatmap:{months}:{metric}`
- TTL: 300秒 (5分钟)
- 失效: 新数据入库时主动清除

---

### 1.2 GET /api/itjuzi/investors/top

**文件位置：** `agent/routers/itjuzi.py` (新增路由)

**请求参数：**
```
GET /api/itjuzi/investors/top?days=90&limit=20&industry=人工智能
```

| 参数 | 类型 | 必填 | 默认值 | 校验规则 |
|------|------|------|--------|----------|
| days | integer | 否 | 90 | 1 ≤ days ≤ 365 |
| limit | integer | 否 | 20 | 1 ≤ limit ≤ 100 |
| industry | string | 否 | - | 行业筛选 |

**响应格式 (200 OK)：**
```json
{
  "code": 0,
  "data": [
    {
      "name": "红杉中国",
      "deal_count": 12,
      "lead_count": 5,
      "total_amount": 45.8,
      "avg_amount": 3.82,
      "industries": ["人工智能", "企业服务", "医疗健康"],
      "rounds": {"A轮": 4, "B轮": 5, "C轮": 3},
      "recent_deals": [
        {
          "company": "XX科技",
          "round": "B轮",
          "date": "2026-06-28",
          "amount": "2亿人民币",
          "is_lead": true
        },
        {
          "company": "YY生物",
          "round": "A轮",
          "date": "2026-06-25",
          "amount": "5000万人民币",
          "is_lead": false
        }
      ]
    }
  ]
}
```

**字段说明：**
- `name`: 机构名称
- `deal_count`: 时间范围内总出手次数
- `lead_count`: 领投次数
- `total_amount`: 参投总金额(亿元人民币)
- `avg_amount`: 平均单笔金额(亿元)
- `industries`: 涉及行业列表(去重)
- `rounds`: 各轮次出手次数分布
- `recent_deals`: 最近5笔投资明细(按date降序)
- `recent_deals[].is_lead`: 是否领投

**实现逻辑(Python伪代码)：**
```python
async def get_top_investors(days: int, limit: int, industry: str = None):
    # 1. 查询时间范围内所有含investors的事件
    query = """
        SELECT id, event_date, company_name, round, amount_text,
               amount_cny_est, industry, investors
        FROM itjuzi_investevent
        WHERE event_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
          AND investors IS NOT NULL AND JSON_LENGTH(investors) > 0
    """
    if industry:
        query += " AND industry = %s"

    rows = await db.fetch_all(query, params)

    # 2. 解析investors JSON，按机构名聚合
    investor_map = defaultdict(lambda: {
        "deal_count": 0, "lead_count": 0,
        "total_amount": 0, "industries": set(),
        "rounds": defaultdict(int), "deals": []
    })

    for row in rows:
        investors = json.loads(row["investors"])
        for inv in investors:
            name = inv["name"]
            investor_map[name]["deal_count"] += 1
            if inv.get("is_lead"):
                investor_map[name]["lead_count"] += 1
            investor_map[name]["total_amount"] += row["amount_cny_est"] or 0
            investor_map[name]["industries"].add(row["industry"])
            investor_map[name]["rounds"][row["round"]] += 1
            investor_map[name]["deals"].append({
                "company": row["company_name"],
                "round": row["round"],
                "date": str(row["event_date"]),
                "amount": row["amount_text"],
                "is_lead": inv.get("is_lead", False)
            })

    # 3. 排序取Top N
    sorted_investors = sorted(
        investor_map.items(),
        key=lambda x: x[1]["deal_count"],
        reverse=True
    )[:limit]

    # 4. 格式化返回(recent_deals取最近5条)
    return [format_investor(name, data) for name, data in sorted_investors]
```

**缓存策略：**
- Key: `itjuzi:investors_top:{days}:{limit}:{industry}`
- TTL: 600秒 (10分钟)

---

## 2. Factory端 - 代理层与关注功能

### 2.1 GET /api/investment/heatmap

**文件位置：** `routes/investment.js` (新增路由)

代理到 Agent `GET http://localhost:8000/api/itjuzi/heatmap`，透传query参数。

---

### 2.2 GET /api/investment/investors/top

代理到 Agent `GET http://localhost:8000/api/itjuzi/investors/top`，透传query参数。

附加逻辑：查询当前用户的followed_investors，在返回结果中标记`is_followed`字段。

**响应增强：**
```json
{
  "name": "红杉中国",
  "is_followed": true,
  "..."
}
```

---

### 2.3 POST /api/investment/follow

**鉴权：** 需要登录态(req.user.id)

**请求体：**
```json
{
  "investor_name": "红杉中国"
}
```

**校验：**
- investor_name: 非空字符串，最大200字符
- 去除首尾空格
- 不允许重复关注(UNIQUE约束，返回409)

**响应 (201 Created)：**
```json
{
  "code": 0,
  "message": "关注成功",
  "data": { "investor_name": "红杉中国", "created_at": "2026-06-30T10:00:00Z" }
}
```

---

### 2.4 DELETE /api/investment/follow/:investor_name

**鉴权：** 需要登录态

**响应 (200 OK)：**
```json
{ "code": 0, "message": "已取消关注" }
```

---

### 2.5 GET /api/investment/follow

**鉴权：** 需要登录态

**响应 (200 OK)：**
```json
{
  "code": 0,
  "data": {
    "followed": [
      { "investor_name": "红杉中国", "created_at": "2026-06-28T10:00:00Z" },
      { "investor_name": "IDG资本", "created_at": "2026-06-25T14:30:00Z" }
    ]
  }
}
```

---

### 2.6 POST /api/investment/follow/check-alerts (内部接口)

**触发方式：** Cron定时任务，每小时执行一次

**鉴权：** 内部调用，校验内部token或来源IP

**逻辑流程：**
1. 查询followed_investors表所有被关注机构名(DISTINCT investor_name)
2. 对每个机构名，查询Agent最近1小时内新入库的事件(investors JSON包含该名称)
3. 匹配关注了该机构的user_id列表
4. 写入alerts表：
```sql
INSERT INTO alerts (user_id, type, title, content, metadata, is_read, created_at)
VALUES (?, 'investment_follow', ?, ?, ?, 0, NOW());
```
5. 对在线用户通过WebSocket推送

---

## 3. 数据库变更

### 3.1 新增表 followed_investors

```sql
CREATE TABLE IF NOT EXISTS followed_investors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    investor_name VARCHAR(200) NOT NULL COMMENT '投资机构名称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
    UNIQUE KEY uk_user_investor (user_id, investor_name),
    KEY idx_investor_name (investor_name),
    KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='用户关注的投资机构';
```

---

## 4. 前端规格

### 4.1 Tab结构

**文件位置：** `public/js/investment.js` 中 `loadInvestment()` 函数改造

```html
<div class="investment-container">
  <div class="tab-nav">
    <button class="tab-btn active" onclick="switchInvestmentTab('events')">
      事件列表
    </button>
    <button class="tab-btn" onclick="switchInvestmentTab('heatmap')">
      热力分析
    </button>
    <button class="tab-btn" onclick="switchInvestmentTab('investors')">
      机构追踪
    </button>
  </div>
  <div id="investment-tab-content"></div>
</div>
```

### 4.2 热力分析Tab

**依赖：** ECharts 5.x (CDN引入或已有)

**组件布局：**
```
+------------------------------------------+
|  月份筛选: [3月|6月|12月]                 |
+------------------------------------------+
|  +-------------------------------------+ |
|  |        行业x月份 热力图              | |
|  |        (ECharts heatmap)            | |
|  +-------------------------------------+ |
+--------------------+---------------------+
|  趋势折线图        |    轮次饼图         |
|  (双Y轴)          |    (ring chart)     |
+--------------------+---------------------+
```

**ECharts配置要点：**
```javascript
// 热力图
option = {
  tooltip: { position: 'top' },
  grid: { top: '10%', left: '15%' },
  xAxis: { type: 'category', data: response.months },
  yAxis: { type: 'category', data: response.industries },
  visualMap: {
    min: 0, max: maxVal, calculable: true,
    inRange: { color: ['#f0f9e8', '#bae4bc', '#7bccc4', '#43a2ca', '#0868ac'] }
  },
  series: [{
    type: 'heatmap',
    data: heatmapData, // [[monthIdx, industryIdx, value], ...]
    emphasis: { itemStyle: { shadowBlur: 10 } }
  }]
};

// 趋势折线(双Y轴)
option = {
  xAxis: { type: 'category', data: trend.months },
  yAxis: [
    { type: 'value', name: '事件数' },
    { type: 'value', name: '金额/亿' }
  ],
  series: [
    { name: '事件数', type: 'line', data: trend.event_count, yAxisIndex: 0 },
    { name: '融资金额', type: 'line', data: trend.total_amount, yAxisIndex: 1,
      areaStyle: { opacity: 0.1 } }
  ]
};

// 轮次饼图
option = {
  series: [{
    type: 'pie', radius: ['40%', '70%'],
    data: round_distribution.map(function(r) { return { name: r.round, value: r.count }; })
  }]
};
```

### 4.3 机构追踪Tab

**组件布局：**
```
+------------------------------------------+
|  筛选: 天数[30|60|90|180] 行业[下拉]     |
+------------------------------------------+
|  # | 机构名称 | 出手| 领投| 金额  | 关注  |
|  1 | 红杉中国 | 12 |  5  |45.8亿 |  *   |
|  +--展开: 近期投资-----------------------+
|  | XX科技 B轮 2亿 2026-06-28 [领投]      |
|  | YY生物 A轮 5000万 2026-06-25          |
|  2 | IDG资本  |  9 |  3  |32.1亿 |  o   |
|  ...                                      |
+------------------------------------------+
```

**交互规格：**
- 点击行展开/折叠recent_deals
- 关注按钮：已关注(实心星，点击取消) / 未关注(空心星，点击关注)
- 关注操作需toast提示成功/失败
- 支持按deal_count/total_amount/lead_count排序切换

---

## 5. 错误处理

| 场景 | HTTP状态码 | 错误码 | 消息 |
|------|-----------|--------|------|
| 参数校验失败 | 400 | INVALID_PARAM | 具体字段提示 |
| 未登录(follow操作) | 401 | UNAUTHORIZED | 请先登录 |
| 重复关注 | 409 | DUPLICATE | 已关注该机构 |
| Agent不可用 | 502 | UPSTREAM_ERROR | 数据服务暂不可用 |
| 内部错误 | 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 6. 测试用例

### Agent端
- heatmap正常返回(默认参数)
- heatmap指定months=12
- heatmap metric=amount
- heatmap months超范围(返回400)
- investors/top正常返回
- investors/top带industry筛选
- investors/top无数据时返回空数组
- 缓存命中验证

### Factory端
- 代理heatmap透传正确
- investors/top附加is_followed字段
- follow创建成功(201)
- follow重复(409)
- follow未登录(401)
- unfollow成功
- unfollow不存在的机构(幂等200)
- check-alerts正确生成预警

### 前端
- Tab切换正常
- 热力图渲染(有数据/无数据)
- 趋势图双Y轴正确
- 饼图hover显示详情
- 机构排行展开/折叠
- 关注/取消关注交互
- 筛选条件切换刷新数据
