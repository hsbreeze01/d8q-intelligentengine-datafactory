## Context

D8Q 智能资讯平台由 4 个微服务组成：Factory（前端聚合层）、Agent（数据采集与存储）、Shark（股票分析）、Compass（分析中枢）。用户通过 Factory SPA 访问所有功能，所有 API 调用都经过 Factory 代理层。当前有 9 个用户账号，5 个赛道，日均 API 调用量预估 200 次/用户。

## Goals / Non-Goals

**Goals:**
- 自动采集用户每次 API 调用事件，前端零代码侵入
- 存储原始事件并提供聚合分析能力（按用户/功能/时间）
- 运营分析看板展示功能使用排行、用户活跃度、冷热图
- 事件数据 90 天自动清理，控制存储增长
- 对现有 API 响应时间影响 < 5ms

**Non-Goals:**
- 不做用户会话追踪（session replay）
- 不做漏斗分析、路径分析等高级分析
- 不做实时流式处理（仅批处理聚合）
- 不引入外部分析服务（GA、Mixpanel 等）
- 不做 A/B 测试框架

## Decisions

### D1: 中间件埋点 vs 前端手动埋点

**决策**：Factory `@app.after_request` 中间件自动埋点

**理由**：
- 前端 SPA 有 20+ 个 `api()` 调用点，手动埋点遗漏率高、维护成本大
- 中间件拦截所有 `/api/*` 请求，零遗漏、零维护
- 可直接读取 `session["username"]` 和 `request` 信息，数据完整
- 对前端代码无侵入

**数据采集字段**：
```
user_id      ← session["username"]
event_time   ← 当前时间
method       ← request.method (GET/POST/PUT/DELETE)
path         ← request.path (/api/news, /api/proxy/tracks, ...)
status_code  ← response.status_code
duration_ms  ← 请求处理耗时
user_agent   ← request.headers.get("User-Agent")
```

### D2: 功能归类映射

**决策**：将 API 路径映射为功能名称，用于聚合分析

```python
FUNCTION_MAP = {
    "/api/news": "资讯",
    "/api/proxy/tracks": "赛道",
    "/api/proxy/tracks/heat": "赛道热度",
    "/api/stock/": "个股分析",
    "/api/watchlist": "自选股",
    "/api/report/": "研报",
    "/api/research/": "研报聚合",
    "/api/policy/": "政策分析",
    "/api/weekly/": "周报",
    "/api/user/": "用户设置",
    "/api/content/": "内容创作",
    "/api/prompts": "Prompt管理",
    "/api/tasks": "采集任务",
}
```

未匹配的路径归类为"其他"。

### D3: 事件存储方案

**决策**：Agent SQLite 新建 `user_events` 表

**理由**：
- 复用现有 Agent SQLite 基础设施，无需新增数据库
- 10 用户 × 200 次/日 × 90 天 ≈ 18 万行，SQLite 完全胜任
- 后续可通过聚合表优化查询性能

**表结构**：
```sql
CREATE TABLE IF NOT EXISTS user_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    event_time DATETIME NOT NULL,
    function_name TEXT NOT NULL,
    method TEXT,
    path TEXT,
    status_code INTEGER,
    duration_ms INTEGER
);
CREATE INDEX idx_ue_user_time ON user_events(user_id, event_time);
CREATE INDEX idx_ue_func_time ON user_events(function_name, event_time);
```

### D4: 事件写入方式

**决策**：Factory 中间件写入本地 SQLite（与 Agent 共享同一 DB 文件）

**理由**：
- Factory 已有 `get_db()` 直接连接 Agent 的 `financial_news.db`
- 无需额外的 HTTP 调用给 Agent，性能开销最小
- 写入在 `after_request` 中执行，不阻塞响应返回

### D5: 聚合查询 API

**决策**：Factory 新增 `/api/analytics/*` 端点

```
GET /api/analytics/overview          — 总览：DAU/MAU/总事件数/功能数
GET /api/analytics/functions         — 功能使用排行（按频次降序）
GET /api/analytics/users             — 用户活跃度排名
GET /api/analytics/trends?days=30    — 活跃度趋势（按天）
GET /api/analytics/cold-hot          — 功能冷热图（使用 vs 未使用）
```

### D6: 数据清理策略

**决策**：`user_events` 原始数据保留 90 天，每天首次启动时检查清理

**理由**：
- 90 天足够做月度/季度趋势分析
- 避免无限增长导致 SQLite 性能退化
- 清理逻辑放在 Factory `before_first_request` 中

### D7: 看板展示方案

**决策**：Factory 设置页新增第 4 个子 Tab "运营分析"，使用已有 ECharts 渲染

- 功能使用排行：水平柱状图
- 活跃度趋势：折线图（按天）
- 功能冷热图：网格色块图（用户×功能矩阵）
- 用户画像：表格（用户名、最近活跃、使用功能数、总调用次数）

## Risks / Trade-offs

- **SQLite 写并发**：Factory gunicorn 多 worker 同时写 SQLite 可能出现锁竞争。缓解措施：使用 `WAL` 模式 + 写入超时重试
- **存储增长**：90 天 18 万行可控，但若用户量增长到 100+ 需要引入聚合表或迁移到 PostgreSQL
- **功能归类精度**：路径前缀匹配可能误归类（如 `/api/stock/comprehensive` 和 `/api/stock/quote` 都归为"个股分析"）。当前粒度足够运营使用
- **隐私**：采集的是 API 调用级别行为，不采集页面停留时间、鼠标轨迹等敏感数据。管理员专属功能
