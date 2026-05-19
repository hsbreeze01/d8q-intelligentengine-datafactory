# Tasks: Monitor DB Connection Context Manager Migration

## 1. Refactor Monitor Handlers

- [x] **1.1 Migrate `update_monitor_rule`, `delete_monitor_rule`, and `monitor_status` from `get_db()` to `get_db_ctx()`**
  - In `app.py`, wrap each handler body in `with get_db_ctx() as conn:`
  - Remove all manual `conn.close()` calls from these 3 functions
  - Preserve all `conn.commit()` calls and business logic exactly as-is
  - Indent handler body one level to fit inside `with` block
  - Verify no other `get_db()` (non-ctx) calls remain in the file

## 2. Validate

- [x] **2.1 Run tests and lint**
  - `ruff check app.py` passes with no new errors
  - `pytest` passes with no regressions
