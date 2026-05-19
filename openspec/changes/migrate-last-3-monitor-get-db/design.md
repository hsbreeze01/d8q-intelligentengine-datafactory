# Design: Monitor DB Connection Context Manager Migration

## Overview

Migrate the last 3 monitor API handlers from raw `get_db()` + manual `conn.close()` to the existing `get_db_ctx()` context manager pattern. This is a pure refactor — no behavior change.

## Architecture Decision

**Use existing `get_db_ctx()` context manager** — it is already defined in `app.py` and used by the vast majority of handlers. The monitor handlers are the last holdouts using the raw pattern, likely because they have multiple early returns which previously made manual close() seem necessary. The `with` block handles this automatically.

**Why not a new abstraction**: `get_db_ctx()` already provides exactly what we need (auto-close on block exit, including early returns and exceptions). No new code is warranted.

## Data Flow

No data flow changes. The same SQL queries run against the same database. The only change is connection lifecycle management:

```
Before: conn = get_db() → ... → conn.close() (per return path)
After:  with get_db_ctx() as conn: → ... → auto-close on block exit
```

## Files Modified

| File | Change |
|------|--------|
| `app.py` | Refactor 3 functions: `update_monitor_rule`, `delete_monitor_rule`, `monitor_status` |

### Detailed Changes per Function

### 1. `update_monitor_rule` (~line 1611)

**Before**: `conn = get_db()` at top, multiple `conn.close()` before early returns, final `conn.close()` at end.

**After**: Wrap entire handler body in `with get_db_ctx() as conn:`. Remove all `conn.close()` calls. `conn.commit()` is kept. All early returns become `return` (no close needed — context manager handles it).

### 2. `delete_monitor_rule` (~line 1641)

**Before**: `conn = get_db()`, `conn.close()` on early return (rule not found) and at end.

**After**: Wrap in `with get_db_ctx() as conn:`. Remove both `conn.close()` calls. Keep `conn.commit()`.

### 3. `monitor_status` (~line 1660)

**Before**: `conn = get_db()` at top, `conn.close()` at end of function.

**After**: Wrap in `with get_db_ctx() as conn:`. Remove final `conn.close()`. All query logic unchanged.

## No New Files

No new files, modules, or dependencies are introduced.
