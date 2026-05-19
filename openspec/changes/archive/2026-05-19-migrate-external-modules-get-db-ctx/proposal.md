# Proposal: IMPLEMENT THIS NOW. Two external modules still use raw sqlite3.connect() instead of the app's get_db_ctx() context manager:

1. heat_anomaly.py — line 11: 'conn = sqlite3.connect(DB_PATH)'. This module has its own DB_PATH. Replace with: import get_db_ctx from app.py OR add try/finally to close. Since this is a standalone utility, the simplest fix is to wrap in try/finally ensuring conn.close() is always called even on exceptions.

2. push_service.py — line 21 and line 58: two 'conn = sqlite3.connect(DB_PATH)' calls. Same pattern — wrap each in try/finally to guarantee conn.close().

For each file:
- Add try/finally around every conn = sqlite3.connect() usage
- Ensure conn.close() is in the finally block
- Keep all business logic unchanged
- These are standalone utilities that import DB_PATH directly, so do NOT import from app.py

## Summary
IMPLEMENT THIS NOW. Two external modules still use raw sqlite3.connect() instead of the app's get_db_ctx() context manager:

1. heat_anomaly.py — line 11: 'conn = sqlite3.connect(DB_PATH)'. This module has its own DB_PATH. Replace with: import get_db_ctx from app.py OR add try/finally to close. Since this is a standalone utility, the simplest fix is to wrap in try/finally ensuring conn.close() is always called even on exceptions.

2. push_service.py — line 21 and line 58: two 'conn = sqlite3.connect(DB_PATH)' calls. Same pattern — wrap each in try/finally to guarantee conn.close().

For each file:
- Add try/finally around every conn = sqlite3.connect() usage
- Ensure conn.close() is in the finally block
- Keep all business logic unchanged
- These are standalone utilities that import DB_PATH directly, so do NOT import from app.py

## Motivation

## Expected Behavior

