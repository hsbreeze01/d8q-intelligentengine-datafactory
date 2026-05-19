# Delta Spec: SQLite Connection Lifecycle Management

## ADDED Requirements

### Requirement: Shared Database Context Manager

All modules in the datafactory project SHALL obtain SQLite connections through a shared context manager (`get_db_ctx`) located in a dedicated utility module, not in `app.py`.

#### Scenario: Module accesses SQLite without circular import risk

- **Given** a module outside `app.py` (e.g., `heat_anomaly.py`, `push_service.py`, `llm_creator.py`) needs to read from the financial news database
- **When** the module opens a database connection
- **Then** it SHALL import `get_db_ctx` from `src/datafactory/infrastructure/db_utils.py`
- **And** the connection SHALL be opened via `with get_db_ctx() as conn:`
- **And** the connection SHALL be automatically closed when the `with` block exits, even if an exception occurs

#### Scenario: WAL mode is enabled once at first connection

- **Given** the application starts
- **When** the first `get_db_ctx()` call is made
- **Then** `PRAGMA journal_mode=WAL` SHALL be executed exactly once
- **And** subsequent calls SHALL NOT re-issue the PRAGMA

### Requirement: Eliminate Manual Connection Close

No module in the project SHALL call `sqlite3.connect()` directly followed by manual `conn.close()` without try/finally protection.

#### Scenario: Migrated module has no bare sqlite3.connect

- **Given** a module that previously used `conn = sqlite3.connect(DB_PATH)` + `conn.close()`
- **When** the migration is complete
- **Then** the module SHALL NOT contain any `sqlite3.connect()` call for the shared `DB_PATH`
- **And** the module SHALL NOT contain any manual `conn.close()` call
- **And** all database operations SHALL be inside a `with get_db_ctx() as conn:` block

#### Scenario: Query exception does not leak connection

- **Given** a module performs a database query via `get_db_ctx()`
- **When** the query raises an exception (e.g., table not found, syntax error)
- **Then** the connection SHALL still be closed
- **And** the exception SHALL propagate to the caller

### Requirement: MySQL Ping Connection Safety

The MySQL ping health check in the monitoring subsystem SHALL use try/finally to guarantee connection closure even on query failure.

#### Scenario: MySQL ping query fails after connect

- **Given** the monitor performs a MySQL connectivity check
- **When** `pymysql.connect()` succeeds but `cur.execute("SELECT 1")` raises an exception
- **Then** the connection SHALL be closed via try/finally
- **And** the error SHALL be returned as a monitoring result

### Requirement: Database Health Monitoring Endpoint

The system SHALL expose a `/api/monitor/db-health` endpoint that reports the health of all database connections used by the application.

#### Scenario: Admin checks database health

- **Given** an authenticated admin user
- **When** a GET request is sent to `/api/monitor/db-health`
- **Then** the response SHALL include the SQLite connection status (accessible / inaccessible)
- **And** the response SHALL include the SQLite WAL mode status (enabled / disabled)
- **And** the response SHALL include the SQLite database file size in bytes
- **And** the response SHALL include the MySQL ping status if configured
- **And** the response SHALL be in JSON format with HTTP 200

#### Scenario: Non-admin user checks database health

- **Given** an authenticated non-admin user
- **When** a GET request is sent to `/api/monitor/db-health`
- **Then** the response SHALL be HTTP 403 with an error message

### Requirement: AgentDBReader Connection Context Safety

`AgentDBReader` SHALL use a reusable context manager for all database connections, eliminating scattered try/finally blocks.

#### Scenario: AgentDBReader query fails mid-operation

- **Given** an `AgentDBReader` instance performing a query on the agent's database
- **When** the query execution raises an exception
- **Then** the connection SHALL be closed automatically
- **And** the exception SHALL propagate to the caller
