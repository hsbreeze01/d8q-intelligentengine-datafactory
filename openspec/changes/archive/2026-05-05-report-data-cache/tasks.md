## 1. 缓存基础设施

- [x] 1.1 在 Factory `app.py` 中实现 `ReportCache` 类：内存字典 + TTL + 惰性过期清理
- [x] 1.2 实现 `get(key)` 方法：检查 expire_at，过期返回 None 并删除
- [x] 1.3 实现 `set(key, data, ttl_seconds)` 方法：存储数据 + 过期时间戳
- [x] 1.4 实现 `get_or_fetch(key, fetch_fn, ttl_seconds)` 方法：缓存命中直接返回，未命中调 fetch_fn 后缓存
- [x] 1.5 初始化全局缓存实例 `_report_cache = ReportCache()`

## 2. 研报搜索缓存

- [x] 2.1 修改 `/api/report/search` 路由：用 `report:{keyword}:{limit}` 作为缓存 key
- [x] 2.2 缓存命中时直接返回，未命中时调 `shark_request` 并缓存结果
- [x] 2.3 空结果也缓存，TTL 5 分钟

## 3. 公告查询缓存

- [x] 3.1 在 `_query_one()` 内部，公告调用改为先查缓存
- [x] 3.2 缓存 key 为 `announcement:{stock_code}:{days}`，TTL 15 分钟

## 4. 批量查询优化

- [x] 4.1 修改 `report_stock_query()`：遍历 keywords 拆分为 cached 和 missed 两组
- [x] 4.2 cached 组直接从缓存组装结果，missed 组并发调远端
- [x] 4.3 合并结果按原始 keywords 顺序返回
- [x] 4.4 响应 header 添加 `X-Cache-Hits: {hits}/{total}` 统计

## 5. 验证

- [x] 5.1 测试：首次搜索触发远端调用，相同搜索 30 分钟内命中缓存无远端调用
- [x] 5.2 测试：批量搜索 3 只股票，其中 2 只已缓存，验证仅 1 只触发远端调用
- [x] 5.3 测试：空结果缓存生效，重复搜索不存在的关键词无远端调用
- [x] 5.4 验证前端功能不受影响（搜索、导入、分页、导出 CSV）
