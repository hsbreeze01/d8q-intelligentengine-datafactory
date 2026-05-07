## 1. 数据层 — 监控规则表 + 内置规则

- [x] 1.1 Factory 启动时自动创建 `monitor_rules` 和 `monitor_results` 表（CREATE TABLE IF NOT EXISTS）
- [x] 1.2 插入 4 条内置发布监控规则（builtin=1）：Cookie 有效性、Ghost Browser CDP、发布锁状态、Infopublisher 健康
- [x] 1.3 验证：curl 查询 `/api/monitor/rules` 返回 4 条内置规则

## 2. 后端 — 监控 API 端点

- [x] 2.1 新增 `GET /api/monitor/rules` — 返回所有监控规则列表
- [x] 2.2 新增 `POST /api/monitor/rules` — 创建自定义规则（校验 type/config/severity）
- [x] 2.3 新增 `PUT /api/monitor/rules/<id>` — 更新规则配置（内置规则仅允许 enabled 切换）
- [x] 2.4 新增 `DELETE /api/monitor/rules/<id>` — 删除规则（builtin=1 返回 403）
- [x] 2.5 新增 `GET /api/monitor/status` — 执行检查并返回实时状态（含缓存逻辑）
- [x] 2.6 实现 HTTP 类型检查器：GET config.url，timeout 内 2xx 即通过
- [x] 2.7 实现 System 类型检查器：systemd_status / file_exists / port_open
- [x] 2.8 实现 Custom 类型检查器：调用 config.url + config.judge 表达式判断
- [x] 2.9 验证：curl 测试所有 API 端点功能正确

## 3. 后端 — 服务状态整合

- [x] 3.1 `/api/monitor/status` 整合现有 `/api/service-status` 数据为 services 字段
- [x] 3.2 为每个 HTTP 服务增加响应时间（ms）指标
- [x] 3.3 验证：`/api/monitor/status` 同时返回 services + rules + alert_count

## 4. 前端 — 监控页面

- [x] 4.1 侧边栏新增 `{id:'monitor', icon:'📡', label:'运行监控', role:'admin'}` 入口（在 tasks 和 settings 之间）
- [x] 4.2 新增 `loadMonitor(el)` 函数：顶部告警横幅 + 基础设施面板 + 业务监控面板
- [x] 4.3 告警横幅：有异常时红色"⚠️ N 项异常"，正常时绿色"✅ 系统运行正常"
- [x] 4.4 基础设施面板：7 个服务状态卡片（名称 + 端口 + 状态 + 响应时间），每行一个
- [x] 4.5 业务监控面板：所有规则列表（名称 + 类型 + 状态 + 上次检查时间 + 操作按钮）
- [x] 4.6 自动轮询：30s 刷新一次，页面顶部显示"上次更新: HH:MM:SS"
- [x] 4.7 手动刷新按钮
- [x] 4.8 新增/编辑规则弹窗（名称、类型、配置、告警级别、检查间隔）

## 5. 前端 — 清理迁移

- [x] 5.1 从 `loadDashboard` 中移除 `loadServiceStatus()` 调用
- [x] 5.2 从设置页 `loadSettings` 中移除 `loadServiceStatus()` 调用
- [x] 5.3 注册 `/monitor` 路由

## 6. 验收测试

- [x] 6.1 admin 登录后可在侧边栏看到"运行监控"入口，viewer/editor 不可见
- [x] 6.2 监控页面正确展示 7 个服务状态 + 4 条内置规则
- [x] 6.3 模拟 Cookie 失效场景，监控页面告警横幅变红
- [x] 6.4 创建/编辑/删除自定义规则功能正常
- [x] 6.5 Dashboard 页面不再显示服务状态卡片
- [ ] 6.6 所有改动提交代码并推送到远端
