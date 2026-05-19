# Delta Spec: Database Connection Safety in Standalone Modules

## MODIFIED Requirements

### REQ-001: Connection lifecycle in heat_anomaly.py

The `detect_heat_anomaly()` function in `heat_anomaly.py` SHALL ensure its SQLite
connection is always closed, even when an exception occurs during query execution.

#### Scenario: Query succeeds normally

- **Given** `detect_heat_anomaly()` is called
- **When** the SQL query executes without error
- **Then** the connection SHALL be closed after query results are fetched

#### Scenario: Query raises an exception

- **Given** `detect_heat_anomaly()` is called
- **When** the SQL query raises an exception (e.g. database locked, corrupt)
- **Then** the connection SHALL still be closed via a `finally` block
- **And** the exception SHALL propagate to the caller

---

### REQ-002: Connection lifecycle in push_service._get_push_configs()

The `_get_push_configs()` function in `push_service.py` SHALL ensure its SQLite
connection is always closed, even when an exception occurs.

#### Scenario: Config query succeeds

- **Given** `_get_push_configs()` is called
- **When** the SQL query executes without error
- **Then** the connection SHALL be closed

#### Scenario: Config query raises an exception

- **Given** `_get_push_configs()` is called
- **When** the SQL query raises an exception
- **Then** the connection SHALL be closed via `finally`
- **And** the exception SHALL propagate

---

### REQ-003: Connection lifecycle in push_service.send_daily_brief()

The `send_daily_brief()` function in `push_service.py` SHALL ensure its SQLite
connection is always closed, even when an exception occurs during either the
heat query or the news query.

#### Scenario: Both queries succeed

- **Given** `send_daily_brief()` is called
- **When** both the heat and news SQL queries execute without error
- **Then** the connection SHALL be closed after all queries complete

#### Scenario: Heat query raises an exception

- **Given** `send_daily_brief()` is called
- **When** the first (heat) SQL query raises an exception
- **Then** the connection SHALL be closed via `finally`
- **And** the exception SHALL propagate

#### Scenario: News query raises an exception

- **Given** `send_daily_brief()` is called
- **When** the heat query succeeds but the news query raises an exception
- **Then** the connection SHALL be closed via `finally`
- **And** the exception SHALL propagate

---

## Constraints

- Both modules MUST remain standalone — they SHALL NOT import `get_db_ctx` from `app.py`.
- All existing business logic, function signatures, and return values SHALL remain unchanged.
- Each raw `sqlite3.connect()` usage MUST be wrapped in `try/finally` with `conn.close()` in the `finally` block.
