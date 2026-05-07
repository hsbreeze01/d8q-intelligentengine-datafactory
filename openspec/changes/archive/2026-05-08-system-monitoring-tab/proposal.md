## Why

当前系统监控散落在 Dashboard（服务状态卡片）和设置页（运营分析 tab）中，admin 无法一目了然地掌握系统整体健康状况。发布流程（Infopublisher → 小红书）是最易出问题的环节——Cookie 失效、Ghost Browser 卡死、tab 切换失败等问题频发，但缺乏实时监控和主动告警机制。需要建设独立的系统运行监控页面，聚合基础设施状态 + 业务监控规则，让 admin 能快速定位问题。

## What Changes

- **独立监控 tab**：侧边栏新增"📡 运行监控"页面（admin 角色），从 Dashboard 和设置页移出服务状态功能
- **基础设施状态面板**：整合现有 7 个服务健康检查（HTTP + systemd），增加响应时间、内存占用等基础指标
- **业务监控规则引擎**：可配置的监控检查项，每项包含：检查类型、检查频率、阈值/条件、告警级别
- **首发监控点**：将发布流程（Infopublisher）作为首个业务监控点，监测 Cookie 有效性、Ghost Browser CDP 连通性、发布锁状态、最近发布成功率
- **监控状态 API**：Factory 新增 `/api/monitor/rules`（CRUD）和 `/api/monitor/status`（实时检查结果）端点
- **告警展示**：监控页面顶部展示告警摘要，异常项红色高亮，支持手动刷新和自动轮询

## Capabilities

### New Capabilities
- `monitoring-dashboard`: 独立运行监控页面 — 聚合基础设施状态 + 业务监控规则的统一视图，包含实时状态检查、告警展示、监控规则管理
- `business-monitor-rules`: 业务监控规则引擎 — 可配置的检查项（Cookie 有效性、服务连通性、发布成功率等），支持 CRUD、定时检查、阈值告警

### Modified Capabilities

## Impact

- **前端 SPA**（index.html）：新增侧边栏"📡 运行监控"页面；从 Dashboard 移除 `loadServiceStatus()`；从设置页保留运营分析 tab 但移出服务状态
- **Factory 后端**（app.py）：新增 `/api/monitor/*` 端点；现有 `/api/service-status` 重构为监控引擎的数据源之一
- **Infopublisher**（server.py）：新增 `/api/publish/stats` 端点，返回最近发布统计数据（成功率、最近失败原因）
- **数据存储**：Factory DB 新增 `monitor_rules` 表存储监控规则配置
