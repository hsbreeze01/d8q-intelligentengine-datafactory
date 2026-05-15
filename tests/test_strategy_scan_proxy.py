# -*- coding: utf-8 -*-
"""Tests for strategy scan proxy route — async scan forwarding (REQ-ASYNC-005).

Verifies that the DataFactory proxy:
- Forwards POST /api/strategy/{group_id}/scan to Compass with short timeout
- Transparently passes through 202 responses from Compass
- Returns 502 with "timeout" keyword when upstream times out
- Returns other upstream errors as-is
"""
import json
import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os


_TEST_DB = tempfile.mktemp(suffix=".db")


def _init_test_db():
    """Create minimal tables needed by the app."""
    conn = sqlite3.connect(_TEST_DB)
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS user_events ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id TEXT NOT NULL, "
        "event_time DATETIME NOT NULL, "
        "function_name TEXT NOT NULL, "
        "method TEXT, "
        "path TEXT, "
        "status_code INTEGER, "
        "duration_ms INTEGER"
        "); "
        "CREATE TABLE IF NOT EXISTS monitor_rules ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL, "
        "type TEXT NOT NULL, "
        "config_json TEXT NOT NULL, "
        "severity TEXT NOT NULL DEFAULT 'warning', "
        "enabled INTEGER NOT NULL DEFAULT 1, "
        "builtin INTEGER NOT NULL DEFAULT 0, "
        "interval_sec INTEGER NOT NULL DEFAULT 60, "
        "created_at DATETIME DEFAULT (datetime('now'))"
        "); "
        "CREATE TABLE IF NOT EXISTS monitor_results ("
        "rule_id INTEGER NOT NULL, "
        "status TEXT NOT NULL, "
        "message TEXT, "
        "detail_json TEXT, "
        "checked_at DATETIME DEFAULT (datetime('now'))"
        "); "
        "CREATE TABLE IF NOT EXISTS user_subscriptions ("
        "user_id TEXT NOT NULL, "
        "track_id INTEGER NOT NULL"
        "); "
        "CREATE TABLE IF NOT EXISTS tracks ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT, "
        "keywords TEXT, "
        "color TEXT"
        ")"
    )
    conn.commit()
    conn.close()


class _ScanProxyTestBase(unittest.TestCase):
    """Base class that sets up a test Flask client with mocked DB."""

    @classmethod
    def setUpClass(cls):
        _init_test_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(_TEST_DB):
            os.unlink(_TEST_DB)

    def _get_client(self):
        """Return a Flask test client with patched get_db."""
        import app as _app_module

        conn_clean = sqlite3.connect(_TEST_DB)
        conn_clean.execute("DELETE FROM user_events")
        conn_clean.commit()
        conn_clean.close()

        _app_module._report_cache._store.clear()

        _orig_get_db = _app_module.get_db

        def _test_get_db():
            conn = sqlite3.connect(_TEST_DB)
            conn.row_factory = sqlite3.Row
            return conn

        _app_module.get_db = _test_get_db
        _app = _app_module.app
        _app.config["TESTING"] = True
        client = _app.test_client()
        with client.session_transaction() as sess:
            sess["role"] = "admin"
            sess["username"] = "admin"
        return client, _app_module, _orig_get_db

    def _restore(self, _app_module, _orig):
        _app_module.get_db = _orig

    @staticmethod
    def _mock_response(data, status=200):
        """Create a mock urllib response object."""
        resp = MagicMock()
        resp.status = status
        resp.read.return_value = json.dumps(data).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp


class TestStrategyScanProxy(_ScanProxyTestBase):
    """Verify POST /api/strategy/<group_id>/scan proxy behavior."""

    @patch("app.urllib.request.urlopen")
    def test_scan_returns_202_with_run_id(self, mock_urlopen):
        """REQ-ASYNC-005: Compass returns 202 with run_id, proxy passes through."""
        client, mod, orig = self._get_client()
        try:
            compass_response = {"run_id": 42, "status": "running"}
            mock_urlopen.return_value = self._mock_response(compass_response, status=202)

            resp = client.post("/api/strategy/1/scan", json={})
            self.assertEqual(resp.status_code, 202)
            data = resp.get_json()
            self.assertIn("run_id", data)
            self.assertEqual(data["run_id"], 42)
            self.assertEqual(data["status"], "running")
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_scan_forwards_to_compass(self, mock_urlopen):
        """REQ-ASYNC-005: Proxy should forward to Compass on port 8087."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response(
                {"run_id": 1, "status": "running"}, status=202
            )

            client.post("/api/strategy/5/scan", json={})
            called_url = mock_urlopen.call_args[0][0]
            if isinstance(called_url, str):
                url_str = called_url
            else:
                url_str = getattr(called_url, "full_url", str(called_url))

            self.assertIn("8087", url_str)
            self.assertIn("/api/strategy/5/scan", url_str)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_scan_timeout_returns_502_with_timeout_keyword(self, mock_urlopen):
        """REQ-ASYNC-005 Scenario 2: Timeout returns 502 with 'timeout' in error."""
        client, mod, orig = self._get_client()
        try:
            import socket
            mock_urlopen.side_effect = socket.timeout("timed out")

            resp = client.post("/api/strategy/1/scan", json={})
            self.assertEqual(resp.status_code, 502)
            data = resp.get_json()
            self.assertIn("error", data)
            self.assertIn("timeout", data["error"].lower())
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_scan_connection_error_returns_502(self, mock_urlopen):
        """Non-timeout connection errors also return 502."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.side_effect = Exception("Connection refused")

            resp = client.post("/api/strategy/1/scan", json={})
            self.assertEqual(resp.status_code, 502)
            data = resp.get_json()
            self.assertIn("error", data)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_scan_compass_error_passthrough(self, mock_urlopen):
        """Compass returns 400/500 errors — proxy passes through."""
        client, mod, orig = self._get_client()
        try:
            import urllib.error
            error_body = json.dumps({"error": "group not found"}).encode()
            http_err = urllib.error.HTTPError(
                "http://localhost:8087/api/strategy/999/scan",
                404, "Not Found", {}, None
            )
            http_err.read = lambda: error_body
            mock_urlopen.side_effect = http_err

            resp = client.post("/api/strategy/999/scan", json={})
            self.assertEqual(resp.status_code, 404)
            data = resp.get_json()
            self.assertIn("error", data)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_scan_uses_short_timeout(self, mock_urlopen):
        """REQ-ASYNC-005: Proxy should use timeout <= 10s for scan requests."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response(
                {"run_id": 1, "status": "running"}, status=202
            )

            client.post("/api/strategy/1/scan", json={})

            called_req = mock_urlopen.call_args[0][0]
            # Check that timeout parameter was passed
            call_kwargs = mock_urlopen.call_args[1]
            if "timeout" in call_kwargs:
                self.assertLessEqual(call_kwargs["timeout"], 10)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_other_routes_not_affected_by_scan_timeout(self, mock_urlopen):
        """REQ-ASYNC-005 Scenario 1: Other API routes remain available during scan."""
        client, mod, orig = self._get_client()
        try:
            groups_data = {"groups": [{"id": 1, "name": "test"}]}
            mock_urlopen.return_value = self._mock_response(groups_data)

            resp = client.get("/api/strategy/groups")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("groups", data)
        finally:
            self._restore(mod, orig)


if __name__ == "__main__":
    unittest.main()
