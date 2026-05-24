# -*- coding: utf-8 -*-
"""Tests for spec: service_status and monitor_status APIs driven by infra_assets."""
import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager


# ---------------------------------------------------------------------------
# Fixtures: isolated temp DB with infra_assets + monitor_rules seeded
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path):
    """Create a temp SQLite DB path."""
    return str(tmp_path / "test.db")


@pytest.fixture()
def seeded_db(tmp_db):
    """Create and seed the temp DB with infra_assets and monitor_rules."""
    import app as _app

    @contextmanager
    def _test_ctx():
        conn = sqlite3.connect(tmp_db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # Patch get_db_ctx before calling init functions
    _app.get_db_ctx = _test_ctx
    _app._init_infra_assets()
    _app._init_monitor_tables()

    yield tmp_db, _test_ctx

    # Restore (not critical in test env, but good practice)


def _make_flask_client(seeded_db):
    """Create a Flask test client with admin session."""
    import app as _app
    _app.app.config["TESTING"] = True
    client = _app.app.test_client()
    with client.session_transaction() as sess:
        sess["username"] = "admin"
        sess["role"] = "admin"
    return client


def _mock_all_services(mock_urlopen):
    """Mock urlopen to return OK for all service health endpoints."""
    def _mock_response(url_or_req, **kwargs):
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = json.dumps({"status": "ok"}).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    mock_urlopen.side_effect = _mock_response


# ---------------------------------------------------------------------------
# Scenario: service_status returns correct JSON envelope
# ---------------------------------------------------------------------------
@patch("app.urllib.request.urlopen")
def test_service_status_returns_correct_envelope(mock_urlopen, seeded_db):
    """GET /api/service-status returns {timestamp: str, services: dict}."""
    _mock_all_services(mock_urlopen)
    client = _make_flask_client(seeded_db)

    resp = client.get("/api/service-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "timestamp" in data, "Missing 'timestamp' key"
    assert "services" in data, "Missing 'services' key"
    assert isinstance(data["services"], dict), "services should be a dict"
    assert isinstance(data["timestamp"], str), "timestamp should be a string"


# ---------------------------------------------------------------------------
# Scenario: service_status includes all enabled infra_assets services
# ---------------------------------------------------------------------------
@patch("app.urllib.request.urlopen")
def test_service_status_includes_all_enabled_services(mock_urlopen, seeded_db):
    """GET /api/service-status includes all 6 checkable services from infra_assets."""
    _mock_all_services(mock_urlopen)
    client = _make_flask_client(seeded_db)

    resp = client.get("/api/service-status")
    data = resp.get_json()
    services = data["services"]

    expected_services = {"factory", "agent", "compass", "stockshark",
                         "infopublisher", "ghost_browser"}
    actual_services = set(services.keys())
    assert expected_services.issubset(actual_services), (
        f"Missing services: {expected_services - actual_services}"
    )


# ---------------------------------------------------------------------------
# Scenario: service_status excludes disabled infra_assets
# ---------------------------------------------------------------------------
@patch("app.urllib.request.urlopen")
def test_service_status_excludes_disabled_services(mock_urlopen, seeded_db):
    """Disabled infra_assets records are excluded from service_status response."""
    tmp_db, _test_ctx = seeded_db

    # Disable factory
    with _test_ctx() as conn:
        conn.execute("UPDATE infra_assets SET enabled=0 WHERE name='factory'")
        conn.commit()

    _mock_all_services(mock_urlopen)
    client = _make_flask_client(seeded_db)

    resp = client.get("/api/service-status")
    data = resp.get_json()

    assert "factory" not in data["services"], (
        "Disabled factory service should not appear in response"
    )


# ---------------------------------------------------------------------------
# Scenario: ghost_browser has type cdp not cdp_tunnel
# ---------------------------------------------------------------------------
@patch("app.urllib.request.urlopen")
def test_ghost_browser_type_is_cdp(mock_urlopen, seeded_db):
    """ghost_browser service entry has type 'cdp', not 'cdp_tunnel'."""
    _mock_all_services(mock_urlopen)
    client = _make_flask_client(seeded_db)

    resp = client.get("/api/service-status")
    data = resp.get_json()
    gb = data["services"].get("ghost_browser")

    assert gb is not None, "ghost_browser missing from services"
    assert gb.get("type") == "cdp", (
        f"Expected type='cdp', got type='{gb.get('type')}'"
    )


# ---------------------------------------------------------------------------
# Scenario: monitor_status returns backward-compatible JSON structure
# ---------------------------------------------------------------------------
@patch("app.urllib.request.urlopen")
def test_monitor_status_backward_compatible_structure(mock_urlopen, seeded_db):
    """GET /api/monitor/status returns {services, rules, alert_count, timestamp}."""
    _mock_all_services(mock_urlopen)
    client = _make_flask_client(seeded_db)

    resp = client.get("/api/monitor/status")
    assert resp.status_code == 200
    data = resp.get_json()

    for key in ("services", "rules", "alert_count", "timestamp"):
        assert key in data, f"Missing key '{key}' in monitor_status response"
    assert isinstance(data["services"], dict), "services should be dict"
    assert isinstance(data["rules"], list), "rules should be list"
    assert isinstance(data["alert_count"], int), "alert_count should be int"


# ---------------------------------------------------------------------------
# Scenario: monitor_status ghost_browser uses direct CDP address
# ---------------------------------------------------------------------------
@patch("app.urllib.request.urlopen")
def test_monitor_status_ghost_browser_direct_cdp(mock_urlopen, seeded_db):
    """monitor_status ghost_browser is checked via 49.234.48.221:9222 (not localhost)."""
    # Track what URLs were actually requested
    requested_urls = []

    def _tracking_mock(url_or_req, **kwargs):
        url_str = getattr(url_or_req, "full_url", str(url_or_req))
        requested_urls.append(url_str)
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = json.dumps({"Browser": "Chrome"}).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    mock_urlopen.side_effect = _tracking_mock

    client = _make_flask_client(seeded_db)
    resp = client.get("/api/monitor/status")
    assert resp.status_code == 200

    # Verify that the CDP check URL uses 49.234.48.221:9222, not localhost:9222
    cdp_urls = [u for u in requested_urls if "9222" in u]
    assert len(cdp_urls) > 0, "No CDP URL found in requests"
    for url in cdp_urls:
        assert "49.234.48.221:9222" in url, (
            f"CDP check should use 49.234.48.221:9222, got: {url}"
        )
        assert "localhost:9222" not in url, (
            f"CDP check should NOT use localhost:9222, got: {url}"
        )

    data = resp.get_json()
    gb = data["services"].get("ghost_browser")
    assert gb is not None, "ghost_browser missing from monitor_status services"
    assert gb.get("type") == "cdp", f"Expected type='cdp', got {gb.get('type')}"
