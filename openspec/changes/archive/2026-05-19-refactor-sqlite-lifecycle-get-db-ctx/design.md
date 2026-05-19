# Design: SQLite Connection Lifecycle Context Manager

## Architecture Decision

Introduce a `get_db_ctx()` context manager in `app.py` that wraps `sqlite3.connect` with `try/finally` auto-close. This follows the Python EAFP pattern and eliminates an entire class of resource-leak bugs.

**Why a new function instead of modifying `get_db()`?**  
Changing `get_db()` to return a context manager would break all 60+ call sites simultaneously. Adding a separate function allows incremental migration — each call site can be converted and tested independently.

**Why not use Flask-SQLAlchemy?**  
The project uses raw `sqlite3` throughout. Introducing an ORM would be a much larger change with higher risk. A context manager is the minimal-scope solution.

## Data Flow

```
Before:
  handler() → conn = get_db() → queries → conn.close()  (often missing on error)

After:
  handler() → with get_db_ctx() as conn: → queries → (auto-close on any exit)
```

## Implementation Details

### New function: `get_db_ctx()`

```python
from contextlib import contextmanager

@contextmanager
def get_db_ctx():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()
```

### Migration pattern

Every call site follows one of these existing patterns:

| Pattern | Count | Migration |
|---------|-------|-----------|
| `conn = get_db(); ...; conn.close()` in `try/finally` | ~15 | Replace with `with get_db_ctx() as conn:` |
| `conn = get_db(); ...; conn.close()` no try | ~30 | Replace with `with get_db_ctx() as conn:` |
| `conn = get_db(); ...` (missing close) | ~15 | Replace with `with get_db_ctx() as conn:` |

### Files to modify

- **`app.py`** — Add `get_db_ctx()`, add deprecation comment to `get_db()`, convert high-priority call sites

### Scope: Phase 1 — Critical paths only (~20 call sites)

The following categories are in scope for this change:

1. **Request hooks**: `_track_event` (after_request) — runs on every API call
2. **Init functions**: `_init_monitor_tables`, `_init_events_table` — run at startup
3. **Cleanup function**: `_cleanup_old_events` — runs daily
4. **News API**: `/api/news`, `/api/meta` — highest-traffic endpoints
5. **Track proxy**: `/api/proxy/tracks/*` — high-traffic proxy routes
6. **Weekly report**: `/api/weekly/generate` — uses separate manual `sqlite3.connect`

Out of scope (Phase 2, future change):
- Low-frequency admin routes
- Routes in `compass_pages.py` (separate blueprint)
- Routes in `export_weekly.py` (separate blueprint)

### Deprecation of `get_db()`

`get_db()` remains unchanged in behavior. A comment is added:
```python
# DEPRECATED: Use get_db_ctx() for new code. See get_db_ctx() for auto-close.
def get_db():
```
