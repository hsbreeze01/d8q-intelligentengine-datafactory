# Design: 策略组 UI 按线框图重构

## 架构决策

### 1. 保持 Server-Side Rendering 架构
策略组页面继续使用 Flask + Jinja2 模板渲染，**不引入前端 SPA 路由**。页面间导航通过 `<a>` 链接 + 服务端路由实现，保持与现有 compass_pages.py 一致的模式。

**理由**：
- 现有 6 个策略页面都是 Jinja2 `{% extends "strategy/base.html" %}` 模式
- 项目无前端构建工具，无 Webpack/Vite
- SEO 不相关（内部工具），SSR 更简单可靠

### 2. 线框图 CSS 组件直接移植
线框图 `Strategy_Group_UX_Wireframe.html` 中定义的 CSS 类（`.group-card`、`.event-card`、`.stock-snapshot`、`.lifecycle-badge` 等）直接移植到各模板的 `{% block head %}` 样式中。

**理由**：
- 线框图已经是完整的 CSS + HTML 实现，可直接复用
- 避免重复造轮子
- 保证视觉一致性

### 3. API 数据通过 Compass 代理获取
所有策略组数据继续通过 `compass_request()` 代理到 Compass API (localhost:8087) 获取。新页面（详情、回测、运行管理）需代理对应的 API 端点。

### 4. ECharts 图表在模板内联 JS 渲染
ECharts CDN 已在 `base.html` 引入，各页面的图表逻辑写在模板的 `<script>` 块中，与现有模式一致。

## 数据流

```
用户浏览器
  ↓ 请求页面路由
compass_pages.py (Flask Blueprint)
  ↓ _compass_request() 代理
Compass API (localhost:8087)
  ↓ 返回 JSON
Jinja2 模板渲染
  ↓ HTML + 内联 JS
浏览器展示
  ↓ Tab 切换/异步加载
fetchJSON() → Compass API 代理路由 → 返回局部数据
```

### 新增 API 代理端点

| 路由 | 代理目标 | 用途 |
|------|----------|------|
| `/api/strategy/groups/<id>/stats/` | Compass `/api/strategy/groups/<id>/stats/` | 策略组详情统计数据 |
| `/api/strategy/groups/<id>/backtest/` | Compass `/api/strategy/groups/<id>/backtest/` | 回测数据 |
| `/api/strategy/groups/<id>/runs/` | Compass `/api/strategy/groups/<id>/runs/` | 运行历史 |
| `/api/strategy/groups/<id>/signals/` | Compass `/api/strategy/groups/<id>/signals/` | 今日信号快照 |
| `/api/strategy/groups/<id>/run/trigger/` | Compass POST `/api/strategy/groups/<id>/run/trigger/` | 触发手动执行 |

## 文件变更清单

### 修改文件

| 文件 | 变更说明 |
|------|----------|
| `compass_pages.py` | 新增 3 个页面路由 + 5 个 API 代理路由 |
| `templates/compass/strategy/base.html` | 面包屑组件、lifecycle 样式增强 |
| `templates/compass/strategy/discover.html` | 按线框图重构：4 统计 + 工具栏 + 卡片网格 |
| `templates/compass/strategy/my_strategies.html` | 按线框图重构：4 统计 + event-card 样式 |
| `templates/compass/strategy/event_detail.html` | 按线框图重构：3 Tab（snapshot-grid + 2charts + LLM+news） |
| `templates/compass/strategy/admin_list.html` | 表格→卡片网格布局重构 |
| `templates/compass/strategy/admin_edit.html` | 增加信号规则区块 |

### 新增文件

| 文件 | 说明 |
|------|------|
| `templates/compass/strategy/admin_detail.html` | 策略组详情页（统计+事件+信号快照+ECharts） |
| `templates/compass/strategy/admin_backtest.html` | 回测页（统计+收益曲线+月度收益） |
| `templates/compass/strategy/admin_run.html` | 运行管理页（调度配置+时间线） |

### 不变文件

| 文件 | 说明 |
|------|------|
| `app.py` | 不涉及主应用路由变更 |
| `templates/compass/strategy/404.html` | 无变更 |

## 前端任务说明

> **前端任务需要人工完成**。本 change 的大部分工作是 HTML/CSS/JS 模板编写和 ECharts 图表配置，属于前端 UI 渲染范畴。zsiga 仅执行后端路由和 API 代理相关的任务。模板文件需要人工参照线框图编写。

## 关键设计细节

### event-card 组件（跨页面共用）
```
结构：图标(48x48) + body(名称+meta) + 涨跌幅 + lifecycle badge
样式：border hover 变蓝、shadow、cursor pointer
```

### stock-snapshot 组件（事件详情微观 Tab）
```
结构：header(名称+星级) + indicators grid(2列键值对)
数据：从 /api/events/<id>/micro 获取，前端渲染为卡片网格
```

### 时间线组件（运行管理页）
```
结构：竖线 + 圆点节点 + 时间 + 内容
状态：success(绿) / fail(红) / 默认(蓝)
```
