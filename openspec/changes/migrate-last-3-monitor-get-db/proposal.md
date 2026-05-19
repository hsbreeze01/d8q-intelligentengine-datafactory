# Proposal: Migrate the last 3 remaining 'conn = get_db()' calls in app.py to use 'with get_db_ctx() as conn:' pattern. These are in monitor rule API handlers:

1. update_monitor_rule (line ~1611): Has multiple early returns with conn.close(). Wrap entire handler body in 'with get_db_ctx() as conn:'. Early returns will auto-close via context manager.

2. delete_monitor_rule (line ~1641): Same pattern - multiple early returns with conn.close(). Wrap in 'with get_db_ctx()'.

3. monitor_status (line ~1660): Long function with single get_db(). Wrap in 'with get_db_ctx()'.

Constraints:
- Remove all manual conn.close() calls that are replaced
- Keep all business logic identical
- Keep conn.commit() where it exists
- The get_db_ctx() function already exists, just use it

## Summary
Migrate the last 3 remaining 'conn = get_db()' calls in app.py to use 'with get_db_ctx() as conn:' pattern. These are in monitor rule API handlers:

1. update_monitor_rule (line ~1611): Has multiple early returns with conn.close(). Wrap entire handler body in 'with get_db_ctx() as conn:'. Early returns will auto-close via context manager.

2. delete_monitor_rule (line ~1641): Same pattern - multiple early returns with conn.close(). Wrap in 'with get_db_ctx()'.

3. monitor_status (line ~1660): Long function with single get_db(). Wrap in 'with get_db_ctx()'.

Constraints:
- Remove all manual conn.close() calls that are replaced
- Keep all business logic identical
- Keep conn.commit() where it exists
- The get_db_ctx() function already exists, just use it

## Motivation

## Expected Behavior

