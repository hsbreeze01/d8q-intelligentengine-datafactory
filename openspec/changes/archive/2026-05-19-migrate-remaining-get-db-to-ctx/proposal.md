# Proposal: Fix two issues in app.py:

ISSUE 1: WAL PRAGMA executed on every get_db_ctx() call
- Current: 'conn.execute("PRAGMA journal_mode=WAL")' runs inside get_db_ctx() every time
- Fix: Move WAL setup to module-level or use a flag to run only once

ISSUE 2: 14 remaining 'conn = get_db()' + manual 'conn.close()' calls not migrated
- Lines: 1071, 1084, 1238, 1287, 1300, 1316, 1330, 1343, 1355, 1594, 1613, 1627, 1657, 1676
- Convert ALL of them to 'with get_db_ctx() as conn:' pattern
- Ensure conn.close() is removed where replaced
- Do NOT touch get_db() function definition itself (keep for backward compat)

Constraints:
- Do NOT change any business logic, only connection lifecycle
- Keep all SQL queries identical
- Ensure indentation is correct when wrapping in 'with' blocks
- If a function has multiple get_db() calls, convert each one separately

## Summary
Fix two issues in app.py:

ISSUE 1: WAL PRAGMA executed on every get_db_ctx() call
- Current: 'conn.execute("PRAGMA journal_mode=WAL")' runs inside get_db_ctx() every time
- Fix: Move WAL setup to module-level or use a flag to run only once

ISSUE 2: 14 remaining 'conn = get_db()' + manual 'conn.close()' calls not migrated
- Lines: 1071, 1084, 1238, 1287, 1300, 1316, 1330, 1343, 1355, 1594, 1613, 1627, 1657, 1676
- Convert ALL of them to 'with get_db_ctx() as conn:' pattern
- Ensure conn.close() is removed where replaced
- Do NOT touch get_db() function definition itself (keep for backward compat)

Constraints:
- Do NOT change any business logic, only connection lifecycle
- Keep all SQL queries identical
- Ensure indentation is correct when wrapping in 'with' blocks
- If a function has multiple get_db() calls, convert each one separately

## Motivation

## Expected Behavior

