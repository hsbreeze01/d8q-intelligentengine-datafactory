# -*- coding: utf-8 -*-
"""Tests for spec: monitor_rules initialization fix and CMDB-driven config."""
import json
import sqlite3
import pytest


# ---------------------------------------------------------------------------
# Fixtures: isolated temp DB with infra_assets seeded
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path):
    """Create a temporary SQLite DB and return its path."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.close()
    return db_path


@pytest.fixture()
def patched_ctx(tmp_db, monkeypatch):
    """Patch get_db_ctx to use temp DB."""
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


def _init_both(patched_ctx):
    """Run _init_infra_assets then _init_monitor_tables."""
    import app as _app
    _app._init_infra_assets()
    _app._init_monitor_tables()


# ---------------------------------------------------------------------------
# Scenario: 4 builtin rules inserted on fresh database
# ---------------------------------------------------------------------------
def test_four_builtin_rules_inserted(tmp_db, patched_ctx):
    """After init, exactly 4 builtin monitor rules exist with correct names."""
    _init_both(patched_ctx)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT name FROM monitor_rules WHERE builtin=1 ORDER BY name"
    ).fetchall()
    conn.close()

    names = sorted([r["name"] for r in rows])
    expected = sorted([
        "Ghost Browser CDP 连通性",
        "发布服务健康",
        "发布锁状态",
        "小红书 Cookie 有效性",
    ])
    assert names == expected, f"Expected {expected}, got {names}"
    assert len(names) == 4


# ---------------------------------------------------------------------------
# Scenario: builtin rules are idempotent across multiple calls
# ---------------------------------------------------------------------------
def test_builtin_rules_idempotent(tmp_db, patched_ctx):
    """Calling _init_monitor_tables() twice doesn't duplicate builtin rules."""
    _init_both(patched_ctx)
    _init_both(patched_ctx)

    conn = sqlite3.connect(tmp_db)
    count = conn.execute(
        "SELECT count(*) FROM monitor_rules WHERE builtin=1"
    ).fetchone()[0]
    conn.close()

    assert count == 4, f"Expected 4 builtin rules after double init, got {count}"


# ---------------------------------------------------------------------------
# Scenario: monitor rules config_json contains no hardcoded PUBLISHER_API literal
# ---------------------------------------------------------------------------
def test_no_hardcoded_publisher_api_in_config(tmp_db, patched_ctx):
    """No builtin rule config_json contains 'PUBLISHER_API' as a literal string."""
    _init_both(patched_ctx)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT name, config_json FROM monitor_rules WHERE builtin=1"
    ).fetchall()
    conn.close()

    for row in rows:
        cfg = row["config_json"]
        assert "PUBLISHER_API" not in cfg, (
            f"Rule '{row['name']}' config_json contains hardcoded PUBLISHER_API: {cfg}"
        )


# ---------------------------------------------------------------------------
# Scenario: CDP rule uses direct remote address not localhost tunnel
# ---------------------------------------------------------------------------
def test_cdp_rule_uses_direct_remote_address(tmp_db, patched_ctx):
    """Ghost Browser CDP rule URL uses 49.234.48.221:9222, not localhost:9222."""
    _init_both(patched_ctx)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT config_json FROM monitor_rules WHERE name='Ghost Browser CDP 连通性'"
    ).fetchone()
    conn.close()

    assert row is not None, "CDP rule not found"
    cfg = json.loads(row["config_json"])
    url = cfg.get("url", "")
    assert "49.234.48.221:9222" in url, f"Expected 49.234.48.221:9222 in url, got: {url}"
    assert "localhost:9222" not in url, f"Should NOT contain localhost:9222, got: {url}"


# ---------------------------------------------------------------------------
# Scenario: Cookie rule URL matches infopublisher infra_assets record
# ---------------------------------------------------------------------------
def test_cookie_rule_url_matches_infopublisher_record(tmp_db, patched_ctx):
    """Cookie validation rule URLs use host/port from infra_assets infopublisher row."""
    _init_both(patched_ctx)

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row

    # Get infopublisher infra record
    infra = conn.execute(
        "SELECT host, port FROM infra_assets WHERE name='infopublisher'"
    ).fetchone()
    assert infra is not None, "infopublisher infra_assets row not found"

    # Get Cookie rule config
    rule = conn.execute(
        "SELECT config_json FROM monitor_rules WHERE name='小红书 Cookie 有效性'"
    ).fetchone()
    conn.close()

    assert rule is not None, "Cookie rule not found"
    cfg = json.loads(rule["config_json"])

    expected_prefix = f"http://{infra['host']}:{infra['port']}"
    assert cfg["url"].startswith(expected_prefix), (
        f"Cookie url should start with {expected_prefix}, got {cfg['url']}"
    )
    assert cfg["status_url"].startswith(expected_prefix), (
        f"Cookie status_url should start with {expected_prefix}, got {cfg['status_url']}"
    )
