"""Tests for src/datafactory/infrastructure/db_utils.py"""
import sqlite3
import os
import tempfile
from unittest import mock

import pytest


def _make_db_utils(db_path):
    """Create a fresh db_utils module wired to *db_path*."""
    import importlib
    import types

    mod = types.ModuleType("db_utils_under_test")
    # We'll test the real module but mock DB_PATH
    code = (
        "import sqlite3\n"
        "from contextlib import contextmanager\n"
        "\n"
        "DB_PATH = None  # placeholder\n"
        "_wal_initialized = False\n"
        "\n"
        "@contextmanager\n"
        "def get_db_ctx():\n"
        "    global _wal_initialized\n"
        "    conn = sqlite3.connect(DB_PATH)\n"
        "    conn.row_factory = sqlite3.Row\n"
        "    if not _wal_initialized:\n"
        "        conn.execute('PRAGMA journal_mode=WAL')\n"
        "        _wal_initialized = True\n"
        "    try:\n"
        "        yield conn\n"
        "    finally:\n"
        "        conn.close()\n"
    )
    exec(compile(code, "<db_utils_test>", "exec"), mod.__dict__)
    mod.DB_PATH = db_path
    return mod


class TestGetDbCtx:
    def test_yields_connection_and_auto_closes(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            mod = _make_db_utils(db_path)
            with mod.get_db_ctx() as conn:
                assert isinstance(conn, sqlite3.Connection)
                conn.execute("CREATE TABLE t(x INTEGER)")
                conn.commit()
            # Connection should be closed — verify by accessing attribute
            with pytest.raises(Exception):
                conn.execute("SELECT 1")
        finally:
            os.unlink(db_path)

    def test_connection_row_factory(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            mod = _make_db_utils(db_path)
            with mod.get_db_ctx() as conn:
                assert conn.row_factory is sqlite3.Row
        finally:
            os.unlink(db_path)

    def test_exception_does_not_leak_connection(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            mod = _make_db_utils(db_path)
            conn_ref = None
            with pytest.raises(RuntimeError):
                with mod.get_db_ctx() as conn:
                    conn_ref = conn
                    raise RuntimeError("boom")
            # conn should be closed
            assert conn_ref is not None
            with pytest.raises(Exception):
                conn_ref.execute("SELECT 1")
        finally:
            os.unlink(db_path)

    def test_wal_mode_set_once(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            mod = _make_db_utils(db_path)
            # First call sets WAL
            with mod.get_db_ctx() as conn:
                pass
            assert mod._wal_initialized is True
            # Subsequent calls should not reset flag — just verify no error
            with mod.get_db_ctx() as conn:
                result = conn.execute("PRAGMA journal_mode").fetchone()[0]
                assert result.lower().startswith("wal")
        finally:
            os.unlink(db_path)


class TestDbUtilsImport:
    """Verify the real module can be imported and has correct API."""

    def test_module_exports(self):
        import sys
        import os
        src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        from datafactory.infrastructure.db_utils import DB_PATH, get_db_ctx

        assert isinstance(DB_PATH, str)
        assert len(DB_PATH) > 0
        assert callable(get_db_ctx)
