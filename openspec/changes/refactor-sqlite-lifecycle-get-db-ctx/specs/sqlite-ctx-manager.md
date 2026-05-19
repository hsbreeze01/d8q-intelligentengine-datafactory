# Delta Spec: SQLite Connection Lifecycle Context Manager

## ADDED Requirements

### Requirement: Context Manager for SQLite Connections

The system SHALL provide a `get_db_ctx()` context manager that yields a SQLite connection and guarantees closure on all exit paths (normal, exception, early return).

#### Scenario: Normal execution closes connection

- Given the `get_db_ctx()` context manager is available
- When a caller uses `with get_db_ctx() as conn:` and executes queries successfully
- Then the connection SHALL be closed automatically after the `with` block exits

#### Scenario: Exception during query closes connection

- Given the `get_db_ctx()` context manager is available
- When a caller uses `with get_db_ctx() as conn:` and an exception occurs during query execution
- Then the connection SHALL be closed automatically before the exception propagates

#### Scenario: Connection has WAL journal mode

- Given the `get_db_ctx()` context manager yields a connection
- When the connection is opened
- Then it SHALL have `PRAGMA journal_mode=WAL` applied automatically

#### Scenario: Connection has Row factory

- Given the `get_db_ctx()` context manager yields a connection
- When the connection is opened
- Then it SHALL have `sqlite3.Row` as `row_factory` set automatically

---

### Requirement: Deprecation of Direct get_db() Usage

The existing `get_db()` function SHALL remain available for backward compatibility but MUST carry a deprecation comment indicating new code SHOULD use `get_db_ctx()` instead.

#### Scenario: get_db() still works

- Given legacy code calls `get_db()`
- When a connection is requested
- Then a working SQLite connection SHALL be returned as before

---

### Requirement: High-Frequency API Handlers Use Context Manager

The following API handler categories MUST use `get_db_ctx()` instead of manual `get_db()` + `conn.close()`:

1. **Request lifecycle hooks** (`_track_event` in `@app.after_request`)
2. **News API** (`/api/news`, `/api/meta`)
3. **Track proxy** (`/api/proxy/tracks/*`)
4. **Weekly report** (`/api/weekly/generate`)
5. **Monitor tables init** (`_init_monitor_tables`, `_init_events_table`)
6. **Event cleanup** (`_cleanup_old_events`)

#### Scenario: API handler no longer leaks connections on error

- Given an API handler uses `get_db_ctx()`
- When the handler raises an unhandled exception during database access
- Then the SQLite connection SHALL be closed without leaking

#### Scenario: API handler behavior unchanged

- Given an API handler is migrated to `get_db_ctx()`
- When the handler processes a request
- Then the response payload and status code SHALL be identical to the pre-migration behavior

---

### Requirement: Initialization Functions Use Context Manager

Database initialization functions (`_init_monitor_tables`, `_init_events_table`) SHALL use `get_db_ctx()` instead of manual `get_db()` + `conn.close()`.

#### Scenario: Init table function closes connection on success

- Given `_init_monitor_tables()` is called
- When table creation and seed data insertion complete successfully
- Then the connection SHALL be closed via the context manager

#### Scenario: Init table function closes connection on failure

- Given `_init_events_table()` is called
- When an exception occurs during `CREATE TABLE IF NOT EXISTS`
- Then the connection SHALL be closed before the exception propagates
