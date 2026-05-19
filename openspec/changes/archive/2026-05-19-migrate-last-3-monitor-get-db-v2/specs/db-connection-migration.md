# Delta Spec: Monitor API DB Connection Migration

## MODIFIED Requirements

### Requirement: Monitor rule handlers SHALL use context-managed database connections

The three monitor rule API handlers (`update_monitor_rule`, `delete_monitor_rule`, `monitor_status`) currently use the deprecated `conn = get_db()` pattern which requires manual `conn.close()` calls on every return path. They SHALL be migrated to use the `with get_db_ctx() as conn:` context manager pattern already established throughout the codebase.

#### Scenario: update_monitor_rule auto-closes connection on early return

- **Given** an admin sends a PUT request to `/api/monitor/rules/<rule_id>`
- **When** the rule does not exist (404) or is a builtin rule with only enabled toggle
- **Then** the connection SHALL be closed automatically by the context manager without an explicit `conn.close()` call
- **And** the response and business logic SHALL remain identical

#### Scenario: delete_monitor_rule auto-closes connection on early return

- **Given** an admin sends a DELETE request to `/api/monitor/rules/<rule_id>`
- **When** the rule does not exist (404) or is a builtin rule (403)
- **Then** the connection SHALL be closed automatically by the context manager
- **And** the response and business logic SHALL remain identical

#### Scenario: monitor_status auto-closes connection after full execution

- **Given** an admin sends a GET request to `/api/monitor/status`
- **When** the handler iterates over rules, executes checks, and returns the status response
- **Then** the connection SHALL be closed automatically by the context manager after the response is constructed
- **And** all `conn.commit()` calls within the function SHALL be preserved
- **And** the response payload SHALL remain identical

### Requirement: No remaining usage of deprecated get_db() in app.py

After migration, `app.py` SHALL have zero calls to `conn = get_db()`. The `get_db()` function definition MAY remain for backward compatibility but MUST not be called.

#### Scenario: grep confirms no get_db() usage remains

- **Given** the migration is complete
- **When** searching `app.py` for the pattern `conn = get_db()`
- **Then** zero matches SHALL be found
