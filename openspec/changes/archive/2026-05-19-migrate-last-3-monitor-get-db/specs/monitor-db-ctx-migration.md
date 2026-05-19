# Spec: Monitor DB Connection Context Manager Migration

## MODIFIED Requirements

### Requirement: Monitor Rule API Handlers SHALL use context-managed database connections

The `update_monitor_rule`, `delete_monitor_rule`, and `monitor_status` API handlers SHALL use the existing `get_db_ctx()` context manager for all database access instead of the raw `get_db()` function with manual `conn.close()` calls.

#### Scenario: update_monitor_rule uses context manager

- **Given** a running datafactory application with monitor rules configured
- **When** a PUT request is sent to `/api/monitor/rules/<id>` with a valid rule update payload
- **Then** the handler SHALL acquire the database connection via `with get_db_ctx() as conn:`
- **And** the connection SHALL be automatically released upon exit (normal or early return)
- **And** no manual `conn.close()` call SHALL exist in the handler body
- **And** all business logic (validation, update, commit) SHALL remain identical to the current behavior

#### Scenario: delete_monitor_rule uses context manager

- **Given** a running datafactory application with monitor rules configured
- **When** a DELETE request is sent to `/api/monitor/rules/<id>`
- **Then** the handler SHALL acquire the database connection via `with get_db_ctx() as conn:`
- **And** the connection SHALL be automatically released upon exit (normal or early return)
- **And** no manual `conn.close()` call SHALL exist in the handler body
- **And** all business logic (existence check, delete, commit) SHALL remain identical to the current behavior

#### Scenario: monitor_status uses context manager

- **Given** a running datafactory application with monitor rules and results stored
- **When** a GET request is sent to `/api/monitor/status`
- **Then** the handler SHALL acquire the database connection via `with get_db_ctx() as conn:`
- **And** the connection SHALL be automatically released upon function exit
- **And** no manual `conn.close()` call SHALL exist in the handler body
- **And** all query logic and response formatting SHALL remain identical to the current behavior

### Requirement: Application SHALL NOT use get_db() for new database connections

After this migration, the codebase SHALL have zero remaining calls to the raw `get_db()` function in monitor-related handlers. All database connections in these handlers MUST use the `get_db_ctx()` context manager pattern, consistent with the rest of the codebase.

#### Scenario: No get_db() calls remain in monitor handlers

- **Given** the application source code after migration
- **When** searching for `get_db()` (non-ctx variant) in monitor API handler functions
- **Then** zero matches SHALL be found
- **And** all `get_db_ctx()` usage in monitor handlers SHALL follow the `with get_db_ctx() as conn:` pattern
