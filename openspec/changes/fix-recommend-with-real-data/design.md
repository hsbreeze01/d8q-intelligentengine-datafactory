# Design: 修复推荐页 — 接入真实股票推荐数据

## 架构决策

### 1. 新增 compass 代理层（而非直接前端调用）

**决策**：在 factory app.py 中新增 `compass_request` 代理函数和对应路由，与现有 `shark_request`、`agent_request` 模式保持一致。

**理由**：
- 前端不应直接访问后端多个服务端口，统一通过 factory 代理避免 CORS 和暴露内部端口
- 已有 `shark_request`（→5000）、`agent_request`（→8000）、`_publisher_request`（→8089）三个代理函数，新增 compass 代理符合既有架构模式
- 便于添加认证、限流、缓存等横切关注点

### 2. compass API 常量

```
COMPASS_API = "http://localhost:8087"
```

与现有常量对齐：
- `AGENT_API = "http://localhost:8000"` (dataagent)
- `SHARK_API = "http://localhost:5000"` (stockshark)
- `PUBLISHER_API = "http://localhost:8089"` (publisher)

### 3. 前端 tab 化重构

推荐页从单维度（赛道热度）改为三 tab 布局：
- 默认 tab 切换到"每日荐股"（核心需求）
- 行业板块和赛道热度作为补充维度
- 保持现有赛道热度逻辑不变，仅调整展示位置

### 4. 行业/概念数据暂不改造 stockshark

proposal 中 Task 2（stockshark 缓存改造）不在本次变更范围内，因为：
- stockshark 是独立服务，修改影响面大
- 前端已做降级处理（数据为空显示"暂无数据"）
- 如后续需要可通过独立 change 处理

## 数据流

### 每日荐股数据流

```
Browser → GET /api/proxy/recommendation/daily
       → factory app.py (compass_request)
       → compass :8087 /api/recommendation/daily
       → RecommendationService (量化评分)
       → 返回 JSON [{code, name, score, dimensions, reason, risk}...]
```

### 推荐生成数据流

```
Browser → POST /api/proxy/recommendation/generate (admin only)
       → factory app.py (compass_request)
       → compass :8087 /api/recommendation/generate
       → 触发 DailyAnalysisTask
       → 返回生成结果
```

### 行业板块数据流

```
Browser → GET /api/search/industries/summary
       → factory app.py (shark_request)
       → stockshark :5000 /api/search/industries/summary
       → 返回行业数据或空列表
```

## 需要修改的文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `app.py` | 新增 | 添加 `COMPASS_API` 常量、`compass_request` 函数、`/api/proxy/recommendation/daily` 路由、`/api/proxy/recommendation/generate` 路由 |
| `templates/index.html` | 修改 | 推荐页 `loadRecommend` 函数重构为三 tab 布局，新增每日荐股和行业板块 tab |
| `tests/test_recommend_routes.py` | 修改 | 新增 compass 代理路由测试用例 |

## 前端任务说明

> `templates/index.html` 中的推荐页 UI 重构（tab 切换、股票评分卡片渲染、行业板块展示）属于 **前端任务**，需要人工完成。后端路由和数据准备任务由 zsiga 执行。
