# Design: 数据库资源统一管理与生命周期治理

## 架构决策

### 1. 提取共享 DB 工具模块

**问题**：`get_db_ctx()` 定义在 `app.py` 中，但 `heat_anomaly.py`、`push_service.py`、`llm_creator.py`、`creator.py` 都无法从 `app.py` 导入（循环依赖：这些模块被 `app.py` 直接或间接导入）。

**决策**：将 `get_db_ctx()` 提取到 `src/datafactory/infrastructure/db_utils.py`。

**理由**：
- `src/datafactory/infrastructure/` 已有 `agent_datasource/db_reader.py`，是 DB 基础设施的自然归属
- 该位置对所有模块可导入且无循环依赖
- `app.py`、`heat_anomaly.py`、`push_service.py`、`llm_creator.py`、`creator.py` 全部从该模块导入

### 2. AgentDBReader 添加内部上下文管理器

**问题**：`AgentDBReader` 访问不同的数据库文件（`financial_news.db` 和 `task_store.db`），不能使用共享的 `get_db_ctx(DB_PATH)`。

**决策**：在 `AgentDBReader` 内部添加 `_get_conn(path)` 私有上下文管理器。

**理由**：
- 保留对不同 DB 路径的灵活性
- 将 5 处重复的 try/finally 模式统一为一个方法
- 不引入额外依赖

### 3. MySQL Ping 修复

**问题**：`_execute_system_check` 中 `mysql_ping` 分支的 `conn.close()` 在 try 块内，异常时不执行。

**决策**：包裹 try/finally。

### 4. DB 健康监控端点

**决策**：在 `app.py` 添加 `/api/monitor/db-health` 端点，返回 SQLite 和 MySQL 连接状态。

**理由**：
- 复用已有的 monitor 基础设施和认证逻辑
- 运维可通过现有监控面板查看 DB 健康状态

## 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                    调用方                                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ app.py   │ heat_    │ push_    │ llm_     │ creator.py      │
│          │ anomaly  │ service  │ creator  │                 │
├──────────┴────┬─────┴──────────┴─────────┬┴─────────────────┤
│               │  import get_db_ctx       │                  │
│               ▼                          ▼                  │
│  ┌──────────────────────────────┐  ┌───────────────────┐   │
│  │ db_utils.py                  │  │ db_reader.py      │   │
│  │ get_db_ctx(DB_PATH)          │  │ _get_conn(path)   │   │
│  │ → with ... as conn:          │  │ → with ... as c:  │   │
│  │   auto close on exit/except  │  │   auto close      │   │
│  └──────────┬───────────────────┘  └───────────────────┘   │
│             │ WAL init once                                │
│             ▼                                               │
│  ┌──────────────────────┐  ┌──────────────────────────┐   │
│  │ SQLite (financial_   │  │ SQLite (task_store.db,    │   │
│  │ news.db) WAL mode    │  │ financial_news.db)        │   │
│  └──────────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

DB Health API:
  GET /api/monitor/db-health → {
    sqlite: { status, wal_mode, db_size_bytes },
    mysql:  { status, latency_ms } | null,
    timestamp
  }
```

## 文件变更清单

| 文件 | 变更类型 | 描述 |
|------|----------|------|
| `src/datafactory/infrastructure/db_utils.py` | **新增** | 共享 `get_db_ctx()` 上下文管理器 + `DB_PATH` 常量 |
| `app.py` | 修改 | 删除本地 `get_db_ctx()` 定义和 `_wal_initialized`，改为从 `db_utils` 导入；修复 MySQL ping try/finally；添加 `/api/monitor/db-health` 端点 |
| `heat_anomaly.py` | 修改 | 删除本地 `sqlite3.connect()` + `try/finally: conn.close()`，改为 `with get_db_ctx() as conn:` |
| `push_service.py` | 修改 | 同上，`_get_push_configs()` 和 `send_daily_brief()` 两处 |
| `src/datafactory/content/llm_creator.py` | 修改 | `_fetch_news()` 改为 `with get_db_ctx() as conn:`，删除 `conn.close()` |
| `src/datafactory/content/creator.py` | 修改 | `fetch_news()` 同上 |
| `src/datafactory/infrastructure/agent_datasource/db_reader.py` | 修改 | 添加 `_get_conn(path)` 私有上下文管理器，替换 5 处 try/finally |

## 依赖关系

- `db_utils.py` 无外部依赖（仅 `sqlite3` + `contextlib`）
- 变更顺序：先创建 `db_utils.py`，再逐文件迁移
- 所有变更向后兼容，不改变任何 API 接口
