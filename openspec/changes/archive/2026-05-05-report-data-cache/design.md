## Context

当前 Factory（:8088）的研报搜索完全透传到 StockShark（:5000）：

```
用户请求 → Factory app.py report_stock_query()
         → ThreadPoolExecutor 并发调用 shark_request()
         → 每个关键词 2 次远端调用：/api/report/search + /api/announcement/stock/{code}
         → 返回结果
```

问题：
- 用户 A 搜索"北特科技"，用户 B 5 分钟后再搜"北特科技"，产生 4 次重复远端调用
- 批量搜索 10 只股票 = 20 次远端调用，其中可能大部分数据近期已被获取过
- Factory 使用 gunicorn `-w 2`，单进程内存缓存即可覆盖该 worker 处理的所有请求

约束：
- 研报/公告为公共数据，无需用户隔离
- Factory 前端 `index.html` 已实现分页、导出、摘要展示，API 契约不应变化
- StockShark 不改动

## Goals / Non-Goals

**Goals:**
- 相同关键词在 TTL 内的重复搜索直接返回缓存，零远端调用
- 批量搜索时自动拆分：缓存命中的关键词直接返回，仅对未命中的发起远端请求
- 前端 API 契约不变（`/api/report/stock` 请求/响应格式完全一致）
- 响应 header 中携带缓存命中统计，便于监控和调试

**Non-Goals:**
- 不引入 Redis/DB 缓存 — 内存字典足够（单 worker 或 2 worker 场景）
- 不做缓存预热 — 首次访问触发远端调用后缓存
- 不修改 StockShark 服务
- 不做缓存持久化 — 服务重启后缓存自动清空

## Decisions

### 1. 缓存存储：进程内 Python 字典

**选择**: `{key: {data, expire_at}}` 字典，带 TTL 过期清理

**替代方案**:
- Redis: 引入额外依赖和运维复杂度，当前 2 worker 场景不需要分布式缓存
- SQLite/文件: 序列化开销大，研报数据包含列表和嵌套结构

**理由**: Factory `-w 2` 意味着同一关键词有 50% 概率命中同一 worker 缓存，已能减少一半远端调用。实现简单零依赖。

### 2. 缓存 Key 策略

```
report:{keyword}:{limit}     → 研报缓存
announcement:{stock_code}:{days}  → 公告缓存
```

用元组字符串作为 key，简单且无哈希冲突。

### 3. TTL 设置

- 研报: 30 分钟（研报发布频率低，日级别更新）
- 公告: 15 分钟（公告可能盘中更新）

### 4. 缓存清理策略

惰性清理：每次读取时检查 `expire_at`，过期则删除并重新请求。不做主动定时清理（内存占用可控）。

### 5. 批量查询优化

`report_stock_query()` 改为：
1. 遍历所有 keywords，拆分为 `cached` 和 `missed` 两组
2. `missed` 组并发调远端，`cached` 组直接从缓存读取
3. 合并结果，按原始顺序返回
4. 响应 header `X-Cache-Hits: 5/10` 标记命中情况

## Risks / Trade-offs

- **[2 worker 缓存不共享]** → 可接受。即使只命中 50% 也大幅减少远端调用。若后续扩 worker 数，再考虑 Redis。
- **[内存占用]** → 单条研报结果约 5-10KB，100 个关键词缓存约 1MB。gunicorn worker 内存 50MB+，影响可忽略。
- **[数据时效性]** → 30/15 分钟 TTL 内用户可能看到旧数据。研报场景可接受。
- **[缓存穿透]** → 如果远端 API 返回空结果，也缓存空结果（TTL 5 分钟），避免重复请求不存在的数据。
