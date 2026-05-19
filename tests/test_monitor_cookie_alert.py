# -*- coding: utf-8 -*-
"""Test: simulate Cookie failure and verify alert banner turns red."""

import json
import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os

# Use a temp DB so we don't touch production data
_TEST_DB = tempfile.mktemp(suffix=".db")


def _init_test_db():
    """Create monitor tables and seed builtin rules into test DB."""
    conn = sqlite3.connect(_TEST_DB)
    conn.executescript(
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
        ")"
    )
    builtin_rules = [
        ("小红书 Cookie 有效性", "custom",
         json.dumps({"url": "http://localhost:8089/api/cookie/validate?mode=fast",
                      "judge": "valid", "timeout": 10,
                      "status_url": "http://localhost:8089/api/cookie/status"}),
         "critical", 120),
        ("Ghost Browser CDP 连通性", "http",
         json.dumps({"url": "http://localhost:9222/json/version", "timeout": 5}),
         "critical", 60),
        ("发布锁状态", "system",
         json.dumps({"check": "file_not_exists", "path": "/tmp/d8q_publishing.lock"}),
         "warning", 30),
        ("发布服务健康", "http",
         json.dumps({"url": "http://localhost:8089/api/health", "timeout": 10}),
         "critical", 120),
    ]
    for name, rtype, cfg, sev, interval in builtin_rules:
        conn.execute(
            "INSERT INTO monitor_rules (name,type,config_json,severity,enabled,builtin,interval_sec) "
            "VALUES (?,?,?,?,1,1,?)", (name, rtype, cfg, sev, interval))
    conn.commit()
    conn.close()


class TestMonitorCookieAlert(unittest.TestCase):
    """When Cookie validation fails, the monitor status should report alerts."""

    @classmethod
    def setUpClass(cls):
        _init_test_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(_TEST_DB):
            os.unlink(_TEST_DB)

    def _get_app(self):
        """Create a Flask test app using the temp DB."""
        import app as _app_module
        from contextlib import contextmanager

        # Clear cached results so each test starts fresh
        conn = sqlite3.connect(_TEST_DB)
        conn.execute("DELETE FROM monitor_results")
        conn.commit()
        conn.close()

        # Patch get_db_ctx to use our temp DB
        _orig_get_db_ctx = _app_module.get_db_ctx

        @contextmanager
        def _test_get_db_ctx():
            conn = sqlite3.connect(_TEST_DB)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

        _app_module.get_db_ctx = _test_get_db_ctx
        _app = _app_module.app
        _app.config["TESTING"] = True
        return _app, _app_module, _orig_get_db_ctx

    def _restore_get_db(self, _app_module, _orig_get_db_ctx):
        _app_module.get_db_ctx = _orig_get_db_ctx

    @patch("app.urllib.request.urlopen")
    def test_cookie_failure_triggers_alert(self, mock_urlopen):
        """Simulate Cookie validation returning valid=false and verify alert_count > 0."""
        _app, _app_module, _orig, _orig_ctx = self._get_app()
        try:
            # Mock responses: Cookie validate returns valid=False
            def _mock_response(url_or_req, **kwargs):
                url_str = getattr(url_or_req, "full_url", str(url_or_req))
                resp = MagicMock()
                resp.status = 200
                if "cookie/validate" in url_str:
                    resp.read.return_value = json.dumps({
                        "valid": False,
                        "message": "Cookie 已失效"
                    }).encode()
                elif "cookie/status" in url_str:
                    resp.read.return_value = json.dumps({
                        "expired_fields": ["web_session"],
                        "remaining_days": 0
                    }).encode()
                elif "9222" in url_str:
                    # Ghost browser OK
                    resp.read.return_value = json.dumps({"Browser": "Chrome"}).encode()
                elif "health" in url_str and "8089" in url_str:
                    resp.read.return_value = json.dumps({"status": "ok"}).encode()
                elif "8089" in url_str:
                    resp.read.return_value = json.dumps({"status": "ok"}).encode()
                else:
                    # All other services OK
                    resp.read.return_value = json.dumps({"status": "ok"}).encode()
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            mock_urlopen.side_effect = _mock_response

            with _app.test_client() as client:
                with client.session_transaction() as sess:
                    sess["role"] = "admin"
                    sess["username"] = "admin"

                resp = client.get("/api/monitor/status")
                self.assertEqual(resp.status_code, 200)
                data = resp.get_json()

                # There should be alerts
                self.assertGreater(data["alert_count"], 0,
                                   "Expected alert_count > 0 when Cookie check fails")

                # Find the Cookie rule result
                cookie_rules = [r for r in data["rules"]
                                if "Cookie" in r.get("name", "")]
                self.assertTrue(len(cookie_rules) > 0, "Should have Cookie monitor rule")

                cookie_rule = cookie_rules[0]
                self.assertEqual(cookie_rule["status"], "error",
                                 f"Cookie rule status should be 'error', got '{cookie_rule['status']}'")
                self.assertEqual(cookie_rule["severity"], "critical")
        finally:
            self._restore_get_db(_app_module, _orig, _orig_ctx)

    @patch("app.urllib.request.urlopen")
    def test_cookie_valid_no_alert(self, mock_urlopen):
        """When Cookie is valid, there should be no Cookie-related alert."""
        _app, _app_module, _orig, _orig_ctx = self._get_app()
        try:
            def _mock_response(url_or_req, **kwargs):
                url_str = getattr(url_or_req, "full_url", str(url_or_req))
                resp = MagicMock()
                resp.status = 200
                if "cookie/validate" in url_str:
                    resp.read.return_value = json.dumps({
                        "valid": True,
                        "message": "Cookie 有效"
                    }).encode()
                elif "cookie/status" in url_str:
                    resp.read.return_value = json.dumps({
                        "expired_fields": [],
                        "remaining_days": 30
                    }).encode()
                elif "9222" in url_str:
                    resp.read.return_value = json.dumps({"Browser": "Chrome"}).encode()
                else:
                    resp.read.return_value = json.dumps({"status": "ok"}).encode()
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            mock_urlopen.side_effect = _mock_response

            with _app.test_client() as client:
                with client.session_transaction() as sess:
                    sess["role"] = "admin"
                    sess["username"] = "admin"

                resp = client.get("/api/monitor/status")
                self.assertEqual(resp.status_code, 200)
                data = resp.get_json()

                # Find the Cookie rule result
                cookie_rules = [r for r in data["rules"]
                                if "Cookie" in r.get("name", "")]
                self.assertTrue(len(cookie_rules) > 0)
                cookie_rule = cookie_rules[0]
                self.assertEqual(cookie_rule["status"], "ok",
                                 f"Cookie rule should be 'ok', got '{cookie_rule['status']}'")
        finally:
            self._restore_get_db(_app_module, _orig, _orig_ctx)


if __name__ == "__main__":
    unittest.main()
