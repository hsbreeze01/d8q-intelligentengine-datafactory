"""Shared database utility — centralized SQLite connection context manager."""
import sqlite3
from contextlib import contextmanager

DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"

_wal_initialized = False


@contextmanager
def get_db_ctx():
    """Yield a SQLite connection with row_factory=Row; auto-close on exit.

    WAL mode is enabled exactly once on the first call.
    """
    global _wal_initialized
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not _wal_initialized:
        conn.execute("PRAGMA journal_mode=WAL")
        _wal_initialized = True
    try:
        yield conn
    finally:
        conn.close()
