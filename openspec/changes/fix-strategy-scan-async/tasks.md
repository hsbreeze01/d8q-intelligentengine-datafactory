# Tasks: 策略扫描异步化 + LLM 分析解耦

## 组 1：Compass 扫描异步化（stockcompass 项目）

- [ ] **1.1 改造 scanner.py** — `Scanner.scan()` 增加 `run_id`（复用已有 run 记录）和 `skip_llm`（跳过 LLM 调用）两个可选参数，传递给 Aggregator
- [ ] **1.2 改造 aggregator.py** — `Aggregator.aggregate()` 增加 `skip_llm` 参数；`_trigger_llm_analysis()` 从 ThreadPoolExecutor 改为 fire-and-forget `threading.Thread(daemon=True)`，新增 `_llm_analyze_sync()` 方法封装 LLM 调用和异常处理
- [ ] **1.3 改造 signals.py 扫描路由** — `trigger_scan()` 改为：创建 run 记录 → 启动后台 `threading.Thread` 执行 `_run_scan_background()` → 立即返回 202 + `{run_id, status:"running"}`；新增 `_run_scan_background()` 函数在后台线程中调用 scanner.scan() 并更新 run 状态

## 组 2：Factory 代理层适配（datafactory 项目）

- [ ] **2.1 优化 compass_pages.py 策略代理 timeout** — 对 `/api/strategy/` 路径中匹配 `scan` 的 POST 请求，代理 timeout 从默认值缩短为 10s，确保只等待 run 创建；对 202 响应原样透传

## 组 3：验证

- [ ] **3.1 编写异步扫描集成测试** — 测试扫描触发返回 202 + run_id；测试扫描期间其他 API 不阻塞；测试 LLM 分析失败不影响聚合结果；测试 stale running 记录清理逻辑
- [ ] **3.2 全量测试通过** — `pytest` + `ruff check` 通过
