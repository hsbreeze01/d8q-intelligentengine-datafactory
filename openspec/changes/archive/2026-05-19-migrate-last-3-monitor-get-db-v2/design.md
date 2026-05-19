# Design: Migrate Last 3 Monitor get_db() → get_db_ctx()

## Architecture Decision

Replace the deprecated `conn = get_db()` + manual `conn.close()` pattern in the 3 remaining monitor API handlers with the `with get_db_ctx() as conn:` context manager. This is the same pattern used by 20+ other handlers in `app.py`.

**Rationale:** The `get_db()` function is marked `DEPRECATED` in source. Manual `conn.close()` on early return paths is error-prone — a missed close leaks a SQLite connection. The context manager guarantees cleanup on every exit path (normal return, early return, or exception).

## Affected Functions

| Function | Line | Pattern | Migration Strategy |
|---|---|---|---|
| `update_monitor_rule` | ~1611 | `conn = get_db()` + 3× `conn.close()` | Wrap body in `with get_db_ctx() as conn:`, remove all `conn.close()` |
| `delete_monitor_rule` | ~1641 | `conn = get_db()` + 3× `conn.close()` | Wrap body in `with get_db_ctx() as conn:`, remove all `conn.close()` |
| `monitor_status` | ~1660 | `conn = get_db()` + 1× `conn.close()` | Wrap body in `with get_db_ctx() as conn:`, remove `conn.close()` |

## Migration Pattern

**Before:**
```python
def handler(...):
    conn = get_db()
    rule = conn.execute(...)
    if not rule:
        conn.close()
        return jsonify({...}), 404
    # ... business logic ...
    conn.close()
    return jsonify({...})
```

**After:**
```python
def handler(...):
    with get_db_ctx() as conn:
        rule = conn.execute(...)
        if not rule:
            return jsonify({...}), 404
        # ... business logic ...
        return jsonify({...})
```

Key rules:
- All business logic and `conn.commit()` calls preserved exactly
- All `conn.close()` calls removed (context manager handles it)
- Early returns inside the `with` block are safe — context manager closes on scope exit
- Indentation of the handler body increases by one level inside the `with` block

## Files Modified

- `app.py` — 3 functions refactored (update_monitor_rule, delete_monitor_rule, monitor_status)

## No New Files

No new files, no new dependencies, no schema changes.
