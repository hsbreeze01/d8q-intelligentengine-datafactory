# Tasks: Migrate Remaining get_db() to get_db_ctx()

## Group 1: WAL Pragma Optimization

- [ ] 1.1 Add `_wal_initialized = False` flag and guard `PRAGMA journal_mode=WAL` in `get_db_ctx()` to execute only once per process

## Group 2: Migrate get_db() Call Sites (Batch 1 — lines ~1071–1355)

- [ ] 2.1 Convert get_db() calls at ~lines 1071 and 1084 to `with get_db_ctx() as conn:` blocks, removing manual `conn.close()`
- [ ] 2.2 Convert get_db() call at ~line 1238 to `with get_db_ctx() as conn:` block
- [ ] 2.3 Convert get_db() calls at ~lines 1287, 1300, 1316 to `with get_db_ctx() as conn:` blocks
- [ ] 2.4 Convert get_db() calls at ~lines 1330, 1343, 1355 to `with get_db_ctx() as conn:` blocks

## Group 3: Migrate get_db() Call Sites (Batch 2 — lines ~1594–1676)

- [ ] 3.1 Convert get_db() calls at ~lines 1594, 1613, 1627 to `with get_db_ctx() as conn:` blocks
- [ ] 3.2 Convert get_db() calls at ~lines 1657, 1676 to `with get_db_ctx() as conn:` blocks

## Group 4: Verification

- [ ] 4.1 Run `ruff check app.py` and fix any lint issues introduced by indentation changes
- [ ] 4.2 Run `pytest tests/` to ensure no regressions
- [ ] 4.3 Grep for remaining `get_db()` calls (excluding the function definition and the DEPRECATED comment) to confirm zero remain
