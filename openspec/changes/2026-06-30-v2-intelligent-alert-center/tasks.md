# Tasks: 智能预警中心

## 1. 数据层

- [ ] 1.1 在 `app.py` 启动时创建 `alert_rules` 表 (DDL + 索引) (1 file: `app.py`)
- [ ] 1.2 在 `app.py` 启动时创建 `alerts` 表 (DDL + 索引) (1 file: `app.py`)
- [ ] 1.3 添加默认预警规则初始化逻辑（为admin用户创建4条默认规则）(1 file: `app.py`)

## 2. 后端API — 预警规则

- [ ] 2.1 实现 `GET /api/alert-rules` — 返回当前用户规则列表 (1 file: `app.py`)
- [ ] 2.2 实现 `POST /api/alert-rules` — 创建规则，含参数校验 (1 file: `app.py`)
- [ ] 2.3 实现 `PUT /api/alert-rules/{id}` — 更新规则，含权限检查 (1 file: `app.py`)
- [ ] 2.4 实现 `DELETE /api/alert-rules/{id}` — 删除规则 (1 file: `app.py`)
- [ ] 2.5 实现 `PATCH /api/alert-rules/{id}/toggle` — 切换启用/禁用 (1 file: `app.py`)

## 3. 后端API — 预警查询

- [ ] 3.1 实现 `GET /api/alerts` — 预警列表(分页+筛选) (1 file: `app.py`)
- [ ] 3.2 实现 `GET /api/alerts/unread-count` — 未读计数 (1 file: `app.py`)
- [ ] 3.3 实现 `PATCH /api/alerts/{id}/read` — 标记单条已读 (1 file: `app.py`)
- [ ] 3.4 实现 `PATCH /api/alerts/read-all` — 标记全部已读 (1 file: `app.py`)

## 4. 预警扫描引擎

- [ ] 4.1 创建 `alert_scanner.py` 模块，定义 `scan_all_alerts()` 主函数 (1 file: `alert_scanner.py`)
- [ ] 4.2 实现 `scan_stock_alerts()` — 比对score_history两天评分差异 (1 file: `alert_scanner.py`)
- [ ] 4.3 实现 `scan_track_alerts()` — 检测赛道热度超阈值 (1 file: `alert_scanner.py`)
- [ ] 4.4 实现 `scan_funding_alerts()` — 检测大额融资事件 (1 file: `alert_scanner.py`)
- [ ] 4.5 实现 `scan_policy_alerts()` — 检测重大政策资讯 (1 file: `alert_scanner.py`)
- [ ] 4.6 实现 cooldown 检查逻辑 + last_triggered_at 更新 (1 file: `alert_scanner.py`)
- [ ] 4.7 实现 urgent 预警的邮件推送(复用 push_service.py) (1 file: `alert_scanner.py`)
- [ ] 4.8 在 `scheduler.py` 注册 scan_all_alerts job (interval=30min) (1 file: `scheduler.py`)

## 5. 前端 — 预警页面

- [ ] 5.1 PAGES 数组新增 alert 项 (1 file: `templates/index.html`)
- [ ] 5.2 loaders 注册 `alert: loadAlert` (1 file: `templates/index.html`)
- [ ] 5.3 实现 `loadAlert(el)` — 渲染指标卡+Tab+列表+规则面板 (1 file: `templates/index.html`)
- [ ] 5.4 实现预警列表渲染（severity颜色标记、时间格式化、操作按钮）(1 file: `templates/index.html`)
- [ ] 5.5 实现规则配置面板（规则列表 + 新建/编辑表单 + 开关切换）(1 file: `templates/index.html`)
- [ ] 5.6 实现标记已读和批量已读交互 (1 file: `templates/index.html`)
- [ ] 5.7 点击预警跳转到关联页面（根据context_json中的type+id导航）(1 file: `templates/index.html`)

## 6. 前端 — 侧边栏红点

- [ ] 6.1 修改 `initNav()` 为alert项添加badge元素 (1 file: `templates/index.html`)
- [ ] 6.2 实现 `pollUnreadCount()` 轮询函数 (setInterval 60s) (1 file: `templates/index.html`)
- [ ] 6.3 实现badge显示逻辑(0隐藏, >0显示, >99显示99+) (1 file: `templates/index.html`)

## 7. 集成与测试

- [ ] 7.1 预警扫描与score_history表联调（依赖自选股日报功能）
- [ ] 7.2 端到端测试：创建规则 → 触发条件 → 生成预警 → 前端展示
- [ ] 7.3 邮件推送集成测试（urgent级别）
- [ ] 7.4 性能验证：扫描耗时 < 5min，unread-count < 10ms

## 文件变更清单

| 文件 | 变更类型 |
|------|----------|
| app.py | 修改: 新增7个API路由 + DDL初始化 |
| alert_scanner.py | 新增: 预警扫描引擎 |
| scheduler.py | 修改: 注册alert_scanner job |
| templates/index.html | 修改: 新增预警页面+侧边栏红点 |

## 预估工期: 5天
