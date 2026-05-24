# -*- coding: utf-8 -*-
"""Tests for spec: infra_assets CMDB table creation and builtin data."""
import sqlite3
import pytest


# ---------------------------------------------------------------------------
# Fixtures: isolated temp DB
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path):
    """Create a temporary SQLite DB and return its path."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.close()
    return db_path


@pytest.fixture()
def patched_init(tmp_db, monkeypatch):
    """Patch get_db_ctx to use temp DB, return the connection factory."""
    from contextlib import contextmanager

    @contextmanager
    def _test_ctx():
        conn = sqlite3.connect(tmp_db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    import app as _app
    monkeypatch.setattr(_app, "get_db_ctx", _test_ctx)
    return _test_ctx


def _run_init_infra_assets(patched_init):
    """Call _init_infra_assets using the patched DB context."""
    import app as _app
    _app._init_infra_assets()


def _run_init_monitor_tables(patched_init):
    """Call _init_monitor_tables using the patched DB context."""
    import app as _app
    _app._init_monitor_tables()


# ---------------------------------------------------------------------------
# Scenario: infra_assets table exists after init
# ---------------------------------------------------------------------------
def test_infra_assets_table_exists_after_init(tmp_db, patched_init):
    """After _init_infra_assets(), the infra_assets table exists with all required columns."""
    _run_init_infra_assets(patched_init)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("PRAGMA table_info(infra_assets)")
    columns = {row["name"] for row in cursor.fetchall()}
    conn.close()

    required = {
        "id", "name", "host", "port", "health_path", "service_type",
        "group_name", "env", "enabled", "metadata_json", "created_at", "updated_at",
    }
    assert required.issubset(columns), f"Missing columns: {required - columns}"


# ---------------------------------------------------------------------------
# Scenario: infra_assets table is idempotent
# ---------------------------------------------------------------------------
def test_infra_assets_idempotent(tmp_db, patched_init):
    """Calling _init_infra_assets() twice inserts no duplicate rows."""
    _run_init_infra_assets(patched_init)
    _run_init_infra_assets(patched_init)

    conn = sqlite3.connect(tmp_db)
    count = conn.execute("SELECT count(*) FROM infra_assets").fetchone()[0]
    conn.close()
    assert count == 7, f"Expected 7 rows after double init, got {count}"


# ---------------------------------------------------------------------------
# Scenario: 7 builtin records inserted on fresh database
# ---------------------------------------------------------------------------
def test_seven_builtin_records_inserted(tmp_db, patched_init):
    """Exactly 7 builtin service records are inserted."""
    _run_init_infra_assets(patched_init)

    conn = sqlite3.connect(tmp_db)
    rows = conn.execute("SELECT name FROM infra_assets ORDER BY name").fetchall()
    conn.close()

    names = sorted([r[0] for r in rows])
    expected = sorted(["factory", "agent", "compass", "stockshark",
                        "infopublisher", "ghost_browser", "mysql"])
    assert names == expected, f"Expected {expected}, got {names}"
    assert len(names) == 7


# ---------------------------------------------------------------------------
# Scenario: ghost_browser record uses direct remote CDP address
# ---------------------------------------------------------------------------
def test_ghost_browser_uses_direct_remote_cdp(tmp_db, patched_init):
    """ghost_browser row has host=49.234.48.221, port=9222, service_type=cdp."""
    _run_init_infra_assets(patched_init)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM infra_assets WHERE name='ghost_browser'").fetchone()
    conn.close()

    assert row is not None, "ghost_browser row not found"
    assert row["host"] == "49.234.48.221", f"Expected host=49.234.48.221, got {row['host']}"
    assert row["port"] == 9222, f"Expected port=9222, got {row['port']}"
    assert row["service_type"] == "cdp", f"Expected service_type=cdp, got {row['service_type']}"
    assert row["host"] != "localhost", "host should NOT be localhost"


# ---------------------------------------------------------------------------
# Scenario: mysql record has service_type db
# ---------------------------------------------------------------------------
def test_mysql_has_service_type_db(tmp_db, patched_init):
    """mysql row has service_type='db' and host='localhost'."""
    _run_init_infra_assets(patched_init)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM infra_assets WHERE name='mysql'").fetchone()
    conn.close()

    assert row is not None, "mysql row not found"
    assert row["service_type"] == "db", f"Expected service_type=db, got {row['service_type']}"
    assert row["host"] == "localhost", f"Expected host=localhost, got {row['host']}"
