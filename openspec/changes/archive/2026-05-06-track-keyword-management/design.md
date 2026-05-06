## Context

D8Q 平台已实现赛道驱动的采集任务系统（commit `3aec66e`）。用户可选择赛道创建采集任务，系统基于赛道关键词自动采集。但关键词管理目前只能通过后端 API 操作（`POST/DELETE /api/tracks/{id}/keywords`），无前端入口。

当前架构：
- **Factory**（Flask + Jinja SPA `templates/index.html`）：前端界面，通过代理路由转发到 data-agent
- **Data-agent**（FastAPI）：已提供完整的关键词 CRUD API
- **已有代理**：`GET /api/proxy/tracks` 和 `GET /api/proxy/tracks/{id}/keywords`（只读）
- **缺失代理**：`POST` 和 `DELETE` 的关键词写入代理

## Goals / Non-Goals

**Goals:**
- 在任务管理界面提供赛道关键词的可视化管理入口
- 支持添加新关键词和删除已有关键词
- 操作后即时刷新 UI，无需手动刷新页面

**Non-Goals:**
- 不涉及批量导入/导出关键词（后续迭代）
- 不涉及关键词分组或优先级管理
- 不修改 data-agent 已有的关键词 API 逻辑
- 不涉及赛道本身的 CRUD（赛道创建/删除由其他系统管理）

## Decisions

### 1. 入口位置：采集任务列表中的赛道 badge 区域

**选择**：在 `loadTasks()` 渲染的任务列表中，已关联赛道的任务行内，赛道 badge 旁边加一个"🔧管理"按钮。

**理由**：
- 关键词是赛道的属性，从赛道 badge 入口最直观
- 不需要额外的页面或导航入口
- 只对有 track_id 的任务显示，避免干扰自定义任务

**备选**：独立的赛道管理页面 → 过重，MVP 阶段不必要

### 2. 交互模式：复用 taskModal 模态框

**选择**：复用现有的 `#taskModal` 弹窗机制，弹出关键词管理面板。

**理由**：
- 与现有的新建/编辑任务弹窗风格一致
- 无需引入新的 DOM 结构或样式
- `closeModal()` 已有，关闭逻辑统一

### 3. Factory 代理路由：补全 POST/DELETE

**选择**：在 `app.py` 的 proxy 块中添加 `POST /api/proxy/tracks/{id}/keywords` 和 `DELETE /api/proxy/tracks/{id}/keywords`。

**理由**：
- 保持与现有 GET 代理路由相同的模式（`requests.get` → `requests.post`/`requests.delete`）
- 认证和错误处理复用同一套逻辑
- 前端只需调用 Factory 的 `/api/proxy/` 前缀路由

## Risks / Trade-offs

- **误删关键词风险** → 删除操作无需二次确认（MVP），关键词可随时重新添加，数据-agent 不限制重复添加
- **并发编辑** → 无乐观锁，多人同时编辑可能互相覆盖。当前单用户使用，可接受
- **删除正在使用的关键词** → 已创建的采集任务不会自动更新关键词列表，需手动重启任务或等待下次调度
