# Design: Database Connection Safety in Standalone Modules

## Problem

Two standalone utility modules (`heat_anomaly.py`, `push_service.py`) use raw
`sqlite3.connect()` without `try/finally`. If an exception occurs between
`connect()` and `close()`, the connection leaks — potentially exhausting the
connection pool or leaving WAL locks held.

## Decision

Wrap every `conn = sqlite3.connect(DB_PATH)` / `conn.close()` pair in a
`try/finally` block so `conn.close()` is guaranteed regardless of exceptions.

### Why not import `get_db_ctx` from `app.py`?

Both modules are standalone utilities that define their own `DB_PATH` and may
run outside the Flask process (e.g. `python push_service.py` as a smoke test).
Introducing a cross-module import to `app.py` would:

1. Create a circular dependency risk (`heat_anomaly` imports `push_service`,
   and we don't want `push_service` importing `app`).
2. Break standalone execution by requiring Flask app context.

A simple `try/finally` is the minimal, safe fix.

## Changes

| File | Function | Change |
|---|---|---|
| `heat_anomaly.py` | `detect_heat_anomaly()` | Wrap query block in `try/finally` |
| `push_service.py` | `_get_push_configs()` | Wrap query block in `try/finally` |
| `push_service.py` | `send_daily_brief()` | Wrap query block in `try/finally` |

## Pattern

Before:
```python
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute(...).fetchall()
conn.close()
```

After:
```python
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
try:
    rows = conn.execute(...).fetchall()
finally:
    conn.close()
```

No other code changes. No new files. No new dependencies.
