## ADDED Requirements

### R1: 预警规则创建

**Given** 用户已登录
**When** POST /api/alert-rules 提交规则配置
**Then** 系统创建预警规则并返回规则ID

- rule_type 必须为 stock_score / track_heat / funding_large / policy_major 之一
- condition_json 必须是合法JSON且包含该类型所需字段
- severity 默认 normal，可选 urgent / important / normal
- cooldown_hours 默认 4，范围 1-72
- enabled 默认 1（启用）
- 每用户最多 50 条规则

### R2: 预警规则管理

**Given** 用户已登录且拥有规则
**When** 操作自己的规则（GET/PUT/DELETE/toggle）
**Then** 仅能操作自己创建的规则

- GET /api/alert-rules 返回当前用户所有规则，按创建时间倒序
- PUT 可修改 rule_name, condition_json, severity, cooldown_hours
- DELETE 删除规则（级联将关联alerts的rule_id设null）
- toggle 切换 enabled 状态（0↔1）
- 操作他人规则返回 403

### R3: 定时预警扫描

**Given** scheduler 每 30 分钟触发 scan_all_alerts
**When** 存在已启用的预警规则
**Then** 按类型批量检测并生成预警

- stock_score: 比对 score_history 表最近两天评分，变化绝对值 >= threshold 时触发
- track_heat: 获取最新热度分数，>= threshold 时触发
- funding_large: 查询最近30min新增事件，amount_cny_est >= min_amount_cny 时触发
- policy_major: 查询最近30min新增政策类资讯，AI标注影响=重大时触发
- 触发前检查 cooldown: last_triggered_at + cooldown_hours > now 则跳过
- 触发后更新 last_triggered_at

### R4: 预警写入与推送

**Given** 预警条件被触发
**When** 写入 alerts 表
**Then** 根据 severity 决定推送方式

- 写入字段: user_id, rule_id, alert_type, severity, title, message, context_json
- title 格式: "[类型] 简述" 如 "[个股] 002594 比亚迪评分下降12分"
- context_json 存储关联数据用于前端跳转
- severity=urgent: 额外通过 push_service.py 发送邮件通知
- severity=important/normal: 仅站内显示

### R5: 预警列表查询

**Given** 用户已登录
**When** GET /api/alerts 带分页和筛选参数
**Then** 返回该用户的预警列表

- 支持筛选: type, severity, is_read
- 分页: page(默认1), page_size(默认20, 最大100)
- 排序: created_at DESC
- 仅返回当前用户的预警

### R6: 未读数量查询

**Given** 用户已登录
**When** GET /api/alerts/unread-count
**Then** 返回未读预警总数和按severity分组数量

- 响应格式: {count: N, by_severity: {urgent: X, important: Y, normal: Z}}
- 查询耗时 < 10ms（利用索引）

### R7: 标记已读

**Given** 用户已登录且预警属于该用户
**When** PATCH /api/alerts/{id}/read 或 PATCH /api/alerts/read-all
**Then** 更新 is_read = 1

- 单条: 仅更新指定ID
- 全部: 更新该用户所有 is_read=0 的记录
- 操作他人预警返回 403

### R8: 前端预警页面

**Given** 用户点击侧边栏「预警」
**When** loadAlert(el) 被调用
**Then** 渲染预警列表页面

- 顶部4个指标卡: 今日预警数 / 未读数 / 紧急未读 / 活跃规则数
- Tab切换: 全部 / 个股 / 赛道 / 融资 / 政策
- 列表项: severity颜色标记 + 标题 + 时间 + [查看详情] [标记已读]
- 点击"查看详情": 根据 context_json 跳转关联页面
- 底部"规则配置"按钮: 展开规则管理面板

### R9: 侧边栏未读红点

**Given** 页面已加载
**When** 存在未读预警 (count > 0)
**Then** 侧边栏"预警"项显示红色未读数badge

- 轮询间隔: 60秒
- badge显示逻辑: count=0隐藏, count>0显示数字, count>99显示"99+"
- 紧急预警时badge变红色闪烁

### R10: 性能约束

- 预警扫描job总耗时 < 5min
- alerts表自动清理: 保留最近90天，超出自动DELETE
- 单次unread-count查询 < 10ms
- 邮件推送异步执行，不阻塞扫描流程
