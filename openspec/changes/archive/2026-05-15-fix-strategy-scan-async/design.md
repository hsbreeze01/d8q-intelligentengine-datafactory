# Design: 策略扫描异步化 + LLM 分析解耦

## 架构决策

### 决策 1：使用 threading.Thread 而非 Celery/任务队列

**理由**：项目当前未引入消息队列基础设施。使用 `threading.Thread(daemon=True)` 是最小侵入方案，无需额外依赖或部署变更。gunicorn sync worker 下 daemon 线程随 worker 进程消亡，但扫描任务本身是有状态的（写 DB），worker 重启后 run 记录保持 "running"，可由下次启动时清理。

**风险与缓解**：如果 gunicorn worker 在扫描期间被杀，run 记录会卡在 "running"。缓解方案：启动时检查超过 10 分钟仍为 running 的 run 记录，标记为 "failed"。

### 决策 2：LLM 分析改为 fire-and-forget

**理由**：LLM 分析（DeepSeek 结构化分析 + 摘要生成）每个事件约 15-30s，4 个事件串行需 60-120s。解耦后聚合流程从 ~180s 降至 ~30s。LLM 结果写入 group_event.llm_analysis 字段，前端可延迟加载。

### 决策 3：保留 ThreadPoolExecutor 但仅用于 LLM 隔离

**理由**：移除 `_trigger_llm_analysis` 中的 ThreadPoolExecutor 超时逻辑，改为简单的 Thread fire-and-forget。超时控制交给 LLM 客户端自身的 timeout 参数。

## 数据流

### 改造前
```
Client → POST /scan → [worker 线程阻塞 180s]
  → Scanner.scan() 27s
  → Aggregator.aggregate()
    → 聚合 ~5s
    → _trigger_llm_analysis() × 4 事件，ThreadPoolExecutor 15s timeout（无效）
      → DeepSeek API 串行调用 ~120s
  → 返回结果
```

### 改造后
```
Client → POST /scan → 创建 run → 启动后台线程 → 立即返回 202
  后台线程:
    → Scanner.scan(run_id=N, skip_llm=True) ~30s
    → Aggregator.aggregate(skip_llm=True)
      → 聚合 ~5s
      → 对每个 event 启动 fire-and-forget Thread 做LLM
    → 更新 run status=completed
  LLM Threads (独立):
    → LLMExtractor.analyze_event() ~15-30s/event
    → 更新 group_event.llm_analysis
    → 失败仅 log warning
```

## 需要修改的文件

### d8q-intelligentengine-stockcompass（主要修改）

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `compass/strategy/routes/signals.py` | MODIFY | `trigger_scan()` 改为创建 run + 启动后台线程 + 返回 202；新增 `_run_scan_background()` |
| `compass/strategy/services/scanner.py` | MODIFY | `scan()` 方法增加 `run_id` 和 `skip_llm` 参数 |
| `compass/strategy/services/aggregator.py` | MODIFY | `_trigger_llm_analysis()` 改为 fire-and-forget Thread；`aggregate()` 增加 `skip_llm` 参数 |

### d8q-intelligentengine-datafactory（次要修改）

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `compass_pages.py` | MODIFY | `_strategy_proxy` 对 `/scan` 路径设置 10s timeout |

## 关键实现细节

### signals.py 变更

```python
# trigger_scan: 从同步阻塞改为异步
@bp.route("/strategy/<int:group_id>/scan", methods=["POST"])
def trigger_scan(group_id):
    run_id = db_helpers.create_run(group_id, trigger_type="manual")
    thread = threading.Thread(
        target=_run_scan_background,
        args=(group_id, run_id),
        daemon=True,
    )
    thread.start()
    return jsonify({"run_id": run_id, "status": "running"}), 202

def _run_scan_background(group_id, run_id):
    try:
        scanner = Scanner()
        result = scanner.scan(group_id, run_id=run_id, skip_llm=True)
        db_helpers.update_run(run_id, status="completed", ...)
    except Exception as exc:
        db_helpers.update_run(run_id, status="failed", error_message=str(exc))
```

### aggregator.py 变更

```python
def _trigger_llm_analysis(self, event_id):
    """Fire-and-forget LLM 分析"""
    thread = threading.Thread(
        target=self._llm_analyze_sync,
        args=(event_id,),
        daemon=True,
    )
    thread.start()

def _llm_analyze_sync(self, event_id):
    try:
        extractor = LLMExtractor()
        extractor.analyze_event(event_id)
    except Exception as exc:
        logger.warning("LLM 分析失败 event=%d: %s", event_id, exc)
```

### compass_pages.py 变更

Factory 代理对 scan 请求使用短 timeout（10s），确保只等待 run 创建。

## 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Worker 被 kill 导致扫描中断 | 低（扫描缩短至 ~30s，远小于 300s timeout） | 中 | 启动时清理 stale running 记录 |
| LLM 线程堆积（频繁扫描） | 低 | 中 | 限制并发 LLM 线程数（可后续加 Semaphore） |
| DB 并发写入冲突 | 极低 | 低 | SQLite WAL mode + 单 writer |
