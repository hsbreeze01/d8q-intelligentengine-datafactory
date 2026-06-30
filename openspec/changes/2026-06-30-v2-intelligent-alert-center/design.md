# Design: 智能预警中心

## Architecture

```
scheduler.py (每30min cron)
  |-- scan_stock_alerts()    -> Shark /api/recommendation/daily 比对 score_history
  |-- scan_track_alerts()    -> Agent /api/tracks/heat/latest 比对阈值
  |-- scan_funding_alerts()  -> Agent /api/itjuzi/events 过滤大额事件
  |-- scan_policy_alerts()   -> Agent /api/news?type=policy 过滤重大政策
        |
        v
  alerts 表 (写入新预警)
        |
        |-- urgent --> push_service.py 发邮件
        |-- important/normal --> 等待前端拉取

Frontend (SPA)
  |-- 侧边栏: 定时轮询 GET /api/alerts/unread-count (每60s)
  |-- 预警页: loadAlert() -> 显示列表/规则配置
  |-- 标记已读: PATCH /api/alerts/{id}/read
```

## Data Model

### alert_rules 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| user_id | TEXT | 用户标识 |
| rule_type | TEXT | stock_score / track_heat / funding_large / policy_major |
| rule_name | TEXT | 规则名称 |
| condition_json | TEXT | 条件JSON |
| severity | TEXT | urgent / important / normal |
| enabled | INTEGER | 1=启用 0=禁用 |
| cooldown_hours | INTEGER | 静默期(小时)，默认4 |
| created_at | TIMESTAMP | 创建时间 |
| last_triggered_at | TIMESTAMP | 上次触发时间 |

索引: (user_id, enabled)

### alerts 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| user_id | TEXT | 用户标识 |
| rule_id | INTEGER FK | 关联规则 |
| alert_type | TEXT | 预警类型 |
| severity | TEXT | 紧急程度 |
| title | TEXT | 预警标题 |
| message | TEXT | 详细消息 |
| context_json | TEXT | 关联上下文数据 |
| is_read | INTEGER | 0=未读 1=已读 |
| created_at | TIMESTAMP | 创建时间 |

索引: (user_id, is_read, created_at DESC)

## API Design

### GET /api/alerts
- Params: page, page_size, type, severity, is_read
- Response: {items: [...], total: N}

### GET /api/alerts/unread-count
- Response: {count: 5, by_severity: {urgent: 1, important: 2, normal: 2}}

### PATCH /api/alerts/{id}/read
- 标记单条已读

### PATCH /api/alerts/read-all
- 标记全部已读

### GET /api/alert-rules
- 获取当前用户所有规则

### POST /api/alert-rules
- Body: {rule_type, rule_name, condition_json, severity, cooldown_hours}

### PUT /api/alert-rules/{id}
- 更新规则

### DELETE /api/alert-rules/{id}
- 删除规则

### PATCH /api/alert-rules/{id}/toggle
- 切换启用/禁用

## Rule Condition Format

stock_score: {"stock_code": "002594", "threshold": 10, "direction": "any"}
track_heat: {"track_id": 3, "threshold": 80}
funding_large: {"min_amount_cny": 10000, "industry": "先进制造"}
policy_major: {"track_id": null}

## Frontend Design

### 侧边栏
- PAGES新增: {id:'alert', icon:'🔔', label:'预警', title:'智能预警'}
- 导航中alert项追加未读badge
- setInterval轮询未读数(60s)

### 预警页面(loadAlert)
- 顶部: 4个指标卡(今日预警/未读/紧急/规则数)
- 筛选: Tab按类型(全部/个股/赛道/融资/政策) + 已读/未读
- 列表: 按severity颜色标记(红/黄/灰)，显示标题+摘要+时间+操作
- 点击预警: 跳转到关联页面(如个股分析/赛道/投融资)
- 规则配置: 底部展开面板，表格展示规则列表，支持新建/编辑/删除/开关

## Scheduler Integration

在scheduler.py新增:
- scan_all_alerts job, interval=30min
- 扫描流程: 读取enabled规则 -> 批量获取数据 -> 比对条件 -> 检查cooldown -> 写入alerts -> urgent发邮件
- 超时: 5min
- 归档: alerts超10000条时删除90天前数据
