# Tasks: SQLite Connection Lifecycle Context Manager

## Group 1: Core Infrastructure

- [x] **1.1** Add `from contextlib import contextmanager` import and define `get_db_ctx()` context manager function in `app.py`. Add deprecation comment to existing `get_db()`. Ensure `get_db_ctx()` sets `row_factory = sqlite3.Row` and executes `PRAGMA journal_mode=WAL`.

## Group 2: Startup & Lifecycle Functions

- [x] **2.1** Migrate `_init_monitor_tables()` and `_init_events_table()` to use `get_db_ctx()`. These run once at startup and currently use manual `get_db()` + `conn.close()`.
- [x] **2.2** Migrate `_cleanup_old_events()` to use `get_db_ctx()`. Currently uses manual `get_db()` + `conn.close()` in a try/except.

## Group 3: High-Traffic API Handlers

- [x] **3.1** Migrate `_track_event` (inside `@app.after_request _track_event`) to use `get_db_ctx()`. This runs on every API request and is the highest-priority fix — currently creates/closes a connection on every API call with a bare try/except that can leak.
- [x] **3.2** Migrate `/api/news` and `/api/meta` handlers to use `get_db_ctx()`. Both use `try/finally/conn.close()` — convert to `with get_db_ctx() as conn:`.
- [x] **3.3** Migrate track proxy handlers (`proxy_tracks`, `proxy_tracks_keywords_write`) to use `get_db_ctx()`. These use `get_db()` with manual close — the subscription-check query in `proxy_tracks` is a good candidate.
- [x] **3.4** Migrate `/api/weekly/generate` to use `get_db_ctx()`. Currently creates a separate `sqlite3.connect(DB_PATH)` with manual close — replace with `get_db_ctx()`.

## Group 4: Verification

- [x] **4.1** Run `ruff check app.py` — ensure no lint errors (E701, E702, unused imports, etc.). Run `pytest` to verify no regressions in existing tests (`tests/test_smoke.py`, `tests/test_recommend_routes.py`, etc.).
