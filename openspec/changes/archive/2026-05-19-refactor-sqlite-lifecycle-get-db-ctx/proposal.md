# Proposal: Refactor app.py in d8q-intelligentengine-datafactory to use context manager for SQLite connection lifecycle management.

Current problem: 60+ places use 'conn = get_db()' with manual 'conn.close()', many missing close on error paths.

Changes:
1. Add a new get_db_ctx() context manager function that wraps sqlite3.connect with try/finally auto-close:
   @contextmanager
   def get_db_ctx():
       conn = sqlite3.connect(DB_PATH)
       conn.row_factory = sqlite3.Row
       conn.execute('PRAGMA journal_mode=WAL')
       try:
           yield conn
       finally:
           conn.close()

2. Replace as many 'conn = get_db()' + manual 'conn.close()' patterns as possible with 'with get_db_ctx() as conn:' pattern. Focus on the most critical paths first (API handlers that are called frequently).

3. Keep get_db() function for backward compatibility but add deprecation comment.

The app has 60+ get_db() calls. This change should convert the most impactful ones - prioritize the ones in API route handlers that are called frequently. Do NOT try to convert all 60+ at once if it risks breaking things.

## Summary
Refactor app.py in d8q-intelligentengine-datafactory to use context manager for SQLite connection lifecycle management.

Current problem: 60+ places use 'conn = get_db()' with manual 'conn.close()', many missing close on error paths.

Changes:
1. Add a new get_db_ctx() context manager function that wraps sqlite3.connect with try/finally auto-close:
   @contextmanager
   def get_db_ctx():
       conn = sqlite3.connect(DB_PATH)
       conn.row_factory = sqlite3.Row
       conn.execute('PRAGMA journal_mode=WAL')
       try:
           yield conn
       finally:
           conn.close()

2. Replace as many 'conn = get_db()' + manual 'conn.close()' patterns as possible with 'with get_db_ctx() as conn:' pattern. Focus on the most critical paths first (API handlers that are called frequently).

3. Keep get_db() function for backward compatibility but add deprecation comment.

The app has 60+ get_db() calls. This change should convert the most impactful ones - prioritize the ones in API route handlers that are called frequently. Do NOT try to convert all 60+ at once if it risks breaking things.

## Motivation

## Expected Behavior

