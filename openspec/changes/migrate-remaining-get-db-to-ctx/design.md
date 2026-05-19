# Design: Migrate Remaining get_db() to get_db_ctx()

## Architecture Decision

### WAL PRAGMA optimization

**Decision**: Use a module-level `_wal_set = False` flag. On first `get_db_ctx()` call, execute `PRAGMA journal_mode=WAL` and set the flag to `True`. Subsequent calls skip the pragma.

**Rationale**: `PRAGMA journal_mode=WAL` is a persistent, per-connection setting. While it's cheap, executing it on every context manager invocation is unnecessary overhead and semantically misleading (WAL is set once for the database file, not per-transaction). A flag-based guard is the simplest approach that avoids import-time side effects.

### get_db() migration

**Decision**: Convert all 14 remaining `conn = get_db()` + `conn.close()` call sites to `with get_db_ctx() as conn:` blocks. Each call site is converted independently — if a function has two `get_db()` calls, it gets two separate `with` blocks.

**Rationale**: `get_db_ctx()` guarantees connection closure via `finally`, even on exceptions. Manual `conn.close()` can be skipped if an exception occurs before it. This is a pure lifecycle refactor with zero business logic change.

## Data Flow

No data flow changes. All SQL queries remain identical. The only change is the connection lifecycle wrapper.

## Files to Modify

### app.py

1. **WAL flag**: Add `_wal_initialized = False` module-level variable. In `get_db_ctx()`, guard the `PRAGMA journal_mode=WAL` with `if not _wal_initialized:`.

2. **14 get_db() call sites** (approximate line numbers from proposal):
   - Lines ~1071, ~1084 (two calls in same or adjacent functions)
   - Lines ~1238, ~1287, ~1300, ~1316, ~1330, ~1343, ~1355
   - Lines ~1594, ~1613, ~1627, ~1657, ~1676

   Each conversion follows the pattern:
   ```python
   # BEFORE
   conn = get_db()
   ... SQL operations ...
   conn.close()

   # AFTER
   with get_db_ctx() as conn:
       ... SQL operations ...  # same body, indented one level
   ```

3. **Preserve** the `get_db()` function definition itself (marked DEPRECATED) for backward compatibility.

## No New Files

This change is contained entirely within `app.py`.
