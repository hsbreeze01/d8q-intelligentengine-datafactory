## Context

D8Q 平台有 7 个微服务（Agent、Factory、Compass、Shark、Infopublisher、Ghost Browser、Xvfb），当前通过 Dashboard 页面底部的 `loadServiceStatus()` 展示基础 HTTP/systemd 状态。发布功能（Infopublisher → 小红书）通过浏览器自动化完成，是系统中最脆弱的环节——Cookie 失效、Ghost Browser 卡死、Vue tab 切换失败等问题反复出现，但缺乏统一的监控视图。

现有基础设施：
- **服务状态 API**：`/api/service-status` 检测 5 个 HTTP 服务 + 2 个 systemd 服务的存活性
- **Cookie 状态**：Infopublisher 的 `/api/cookie/status` 和 `/api/cookie/validate`
- **发布锁**：`/tmp/d8q_publishing.lock` 标记发布进行中
- **截图**：`/tmp/xhs_publish_result.png` 记录最后一次发布结果
- 无业务级监控、无告警机制、无历史数据

关键约束：
- 无新增基础设施（无新中间件、无新服务）
- 监控规则存储在 Factory SQLite（复用现有 DB）
- 监控检查通过 HTTP 调用各服务现有端点实现
- 仅 admin 角色可见

## Goals / Non-Goals

**Goals:**
- admin 在一个独立页面看到系统全貌：服务健康 + 业务监控
- 可配置业务监控规则（检查项、阈值、告警级别）
- 首个监控点覆盖发布全链路：Cookie、CDP、发布成功率
- 异常项醒目标记，支持手动刷新
- 从 Dashboard 和设置页移出服务状态，避免功能散落

**Non-Goals:**
- 不做实时推送（WebSocket/SSE），使用定时轮询
- 不做历史监控数据存储和趋势图（本期）
- 不做自动故障恢复
- 不做非 admin 角色的监控视图

## Decisions

### D1: 监控页面位置 — 独立侧边栏 tab

**选择**：在侧边栏"任务"和"设置"之间新增"📡 运行监控"页面，仅 admin 可见。

**理由**：
- 监控是运维操作，与"设置"（系统配置）和"任务"（内容任务管理）逻辑独立
- admin 需要快速访问，放在侧边栏一级入口

### D2: 监控规则存储 — Factory SQLite

**选择**：新增 `monitor_rules` 表存储规则配置，`monitor_results` 表缓存最近检查结果。

**理由**：
- 无新基础设施，复用 Factory 现有 DB
- 规则数量有限（<20 条），SQLite 足够

**表结构**：
```
monitor_rules(id, name, type, config_json, severity, enabled, interval_sec, last_check, created_at)
monitor_results(rule_id, status, message, detail_json, checked_at)
```

### D3: 检查执行 — Factory API 层定时轮询

**选择**：前端 30s 轮询 `/api/monitor/status`，后端按规则 `interval_sec` 缓存检查结果（避免每次请求都执行检查）。

**理由**：
- 简单可靠，无 WebSocket 复杂度
- 缓存机制避免高频检查压垮被监控服务

### D4: 首发监控点 — 发布全链路

**选择**：内置 4 个默认监控规则（不可删除）：
1. **Cookie 有效性** — 调用 `/api/cookie/validate`
2. **Ghost Browser CDP** — 调用 `http://localhost:9222/json/version`
3. **发布锁状态** — 检查 `/tmp/d8q_publishing.lock` 是否存在超过 10 分钟
4. **Infopublisher 健康** — 调用 `/api/health`

**理由**：覆盖发布流程最易失败的 4 个环节。

### D5: 规则类型 — HTTP + SYSTEM + CUSTOM

**选择**：支持 3 种检查类型：
- `http`：HTTP GET 请求，检查状态码/响应内容
- `system`：系统级检查（systemd 状态、文件存在性、端口连通性）
- `custom`：调用特定 API 端点，解析 JSON 判断状态

**理由**：覆盖从基础设施到业务逻辑的所有检查场景。

## Risks / Trade-offs

- **[无历史数据]** → 本期只展示当前状态快照，不追踪趋势。后续可加 `monitor_history` 表
- **[轮询频率]** → 默认 30s 前端轮询 + 后端按规则间隔缓存，平衡实时性和性能
- **[Ghost Browser 稳定性]** → CDP 检查可能因 Ghost Browser 卡死而超时，设置 5s 超时上限
- **[规则误配]** → 内置规则不可删除/修改核心参数，自定义规则可自由编辑
