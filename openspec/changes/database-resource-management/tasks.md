# Tasks: 数据库资源统一管理与生命周期治理

## Group 1: 基础设施 — 共享 DB 工具模块

- [x] **1.1** 创建 `src/datafactory/infrastructure/db_utils.py` — 提取 `DB_PATH` 常量和 `get_db_ctx()` 上下文管理器（含 WAL 一次性初始化），从 `app.py` 原样搬迁逻辑，保持 `_wal_initialized` 全局标志

## Group 2: app.py 迁移 + MySQL 安全修复

- [ ] **2.1** 重构 `app.py` 的 DB 导入 — 删除本地 `get_db_ctx()` 定义和 `_wal_initialized` 全局变量，改为 `from datafactory.infrastructure.db_utils import get_db_ctx, DB_PATH`；验证所有现有 `with get_db_ctx()` 调用点不受影响
- [ ] **2.2** 修复 `_execute_system_check()` 中 `mysql_ping` 分支的连接泄漏 — 将 `pymysql.connect()` + `cur.execute()` + `conn.close()` 改为 try/finally 模式确保异常时连接关闭
- [ ] **2.3** 添加 `/api/monitor/db-health` 端点 — 返回 SQLite 状态（WAL 模式、文件大小、可连通性）和 MySQL ping 状态（延迟毫秒），限 admin 角色

## Group 3: 辅助模块迁移（heat_anomaly / push_service）

- [ ] **3.1** 重构 `heat_anomaly.py` — `detect_heat_anomaly()` 中 `sqlite3.connect(DB_PATH)` + try/finally:conn.close() 改为 `from datafactory.infrastructure.db_utils import get_db_ctx` + `with get_db_ctx() as conn:`
- [ ] **3.2** 重构 `push_service.py` — `_get_push_configs()` 和 `send_daily_brief()` 两处 `sqlite3.connect(DB_PATH)` + try/finally:conn.close() 改为 `with get_db_ctx() as conn:`

## Group 4: 内容创作模块迁移（llm_creator / creator）

- [ ] **4.1** 重构 `llm_creator.py` 的 `_fetch_news()` — 删除 `sqlite3.connect(DB_PATH)` + `conn.close()`，改为 `with get_db_ctx() as conn:`（注意：`DB_PATH` 不再需要本地定义，从 db_utils 导入）
- [ ] **4.2** 重构 `creator.py` 的 `fetch_news()` — 同 4.1 模式，删除本地 `DB_PATH` 和 `sqlite3.connect()` + `conn.close()`

## Group 5: AgentDBReader 连接安全

- [ ] **5.1** 重构 `db_reader.py` — 在 `AgentDBReader` 内部添加 `_get_conn(db_path)` 私有上下文管理器，替换 `_query_news()`、`count_news()`、`list_scheduled_tasks()`、`get_recent_executions()` 中 5 处重复的 try/finally:conn.close() 模式
