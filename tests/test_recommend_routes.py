# -*- coding: utf-8 -*-
"""Tests for recommend page backend proxy routes (Task 2.1).

Verifies that the three existing proxy routes used by the recommend page
return valid data when their upstream services respond correctly.
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


class _RecommendRouteTestBase(unittest.TestCase):
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

        # Clear report cache so each test starts fresh
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


class TestStockReportsRoute(_RecommendRouteTestBase):
    """Verify GET /api/stock/reports proxies to StockShark correctly."""

    @patch("app.urllib.request.urlopen")
    def test_reports_proxy_returns_data(self, mock_urlopen):
        """Route should proxy to shark /api/report/search and return reports."""
        client, mod, orig = self._get_client()
        try:
            reports_data = {
                "reports": [
                    {
                        "title": "新能源汽车行业深度报告",
                        "org": "中信证券",
                        "date": "2025-01-15",
                        "category": "行业研究",
                        "summary": "新能源车渗透率持续提升",
                    },
                    {
                        "title": "固态电池产业化进展",
                        "org": "国泰君安",
                        "date": "2025-01-14",
                        "category": "技术分析",
                    },
                ]
            }
            mock_urlopen.return_value = self._mock_response(reports_data)

            resp = client.get("/api/stock/reports?keyword=&limit=10")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("reports", data)
            self.assertEqual(len(data["reports"]), 2)
            self.assertEqual(data["reports"][0]["org"], "中信证券")
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_reports_forwards_keyword_and_limit(self, mock_urlopen):
        """Route should forward keyword and limit params to StockShark."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response({"reports": []})

            client.get("/api/stock/reports?keyword=%E6%96%B0%E8%83%BD%E6%BA%90&limit=5")

            called_url = mock_urlopen.call_args[0][0]
            if isinstance(called_url, str):
                url_str = called_url
            else:
                url_str = getattr(called_url, "full_url", str(called_url))

            self.assertIn("/api/report/search", url_str)
            self.assertIn("keyword=", url_str)
            self.assertIn("limit=5", url_str)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_reports_empty_result_returns_valid_json(self, mock_urlopen):
        """Route should handle empty results gracefully."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response({"reports": []})

            resp = client.get("/api/stock/reports?keyword=&limit=10")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("reports", data)
            self.assertEqual(len(data["reports"]), 0)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_reports_upstream_error_returns_502(self, mock_urlopen):
        """Route should return 502 when upstream StockShark is unreachable."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.side_effect = Exception("Connection refused")

            resp = client.get("/api/stock/reports?keyword=&limit=10")
            self.assertEqual(resp.status_code, 502)
            data = resp.get_json()
            self.assertIn("error", data)
        finally:
            self._restore(mod, orig)


class TestTrackHeatRoute(_RecommendRouteTestBase):
    """Verify GET /api/proxy/tracks/heat/latest proxies to agent correctly."""

    @patch("app.urllib.request.urlopen")
    def test_track_heat_returns_data(self, mock_urlopen):
        """Route should proxy to agent /api/tracks/heat/latest."""
        client, mod, orig = self._get_client()
        try:
            heat_data = [
                {"id": 1, "name": "人工智能", "score": 85, "change": 12.5, "color": "#1890ff"},
                {"id": 2, "name": "新能源", "score": 72, "change": -3.2, "color": "#52c41a"},
            ]
            mock_urlopen.return_value = self._mock_response(heat_data)

            resp = client.get("/api/proxy/tracks/heat/latest")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["name"], "人工智能")
            self.assertEqual(data[0]["score"], 85)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_track_heat_forwards_correct_url(self, mock_urlopen):
        """Route should strip /api/proxy/ prefix and forward to agent."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response([])

            client.get("/api/proxy/tracks/heat/latest")

            called_url = mock_urlopen.call_args[0][0]
            if isinstance(called_url, str):
                url_str = called_url
            else:
                url_str = getattr(called_url, "full_url", str(called_url))

            self.assertIn("/api/tracks/heat/latest", url_str)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_track_heat_empty_result(self, mock_urlopen):
        """Route should handle empty track heat data."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response([])

            resp = client.get("/api/proxy/tracks/heat/latest")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 0)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_track_heat_upstream_error(self, mock_urlopen):
        """Route should return 502 when agent is unreachable."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.side_effect = Exception("Connection refused")

            resp = client.get("/api/proxy/tracks/heat/latest")
            self.assertEqual(resp.status_code, 502)
            data = resp.get_json()
            self.assertIn("error", data)
        finally:
            self._restore(mod, orig)


class TestSearchByKeywordRoute(_RecommendRouteTestBase):
    """Verify GET /api/search/by-keyword proxies to StockShark correctly."""

    @patch("app.urllib.request.urlopen")
    def test_search_by_keyword_returns_data(self, mock_urlopen):
        """Route should proxy to shark /api/search/stock/by-keyword."""
        client, mod, orig = self._get_client()
        try:
            search_data = {
                "data": [
                    {"code": "002594", "name": "比亚迪", "change_pct": 2.35},
                    {"code": "300750", "name": "宁德时代", "change_pct": -1.12},
                ]
            }
            mock_urlopen.return_value = self._mock_response(search_data)

            resp = client.get("/api/search/by-keyword?keyword=%E6%96%B0%E8%83%BD%E6%BA%90&limit=20")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("data", data)
            self.assertEqual(len(data["data"]), 2)
            self.assertEqual(data["data"][0]["code"], "002594")
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_search_by_keyword_forwards_params(self, mock_urlopen):
        """Route should forward keyword and limit to StockShark."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response({"data": []})

            client.get("/api/search/by-keyword?keyword=%E6%96%B0%E8%83%BD%E6%BA%90&limit=20")

            called_url = mock_urlopen.call_args[0][0]
            if isinstance(called_url, str):
                url_str = called_url
            else:
                url_str = getattr(called_url, "full_url", str(called_url))

            self.assertIn("/api/search/stock/by-keyword", url_str)
            self.assertIn("keyword=", url_str)
            self.assertIn("limit=20", url_str)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_search_by_keyword_empty_result(self, mock_urlopen):
        """Route should handle no results gracefully."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.return_value = self._mock_response({"data": []})

            resp = client.get("/api/search/by-keyword?keyword=%E4%B8%8D%E5%AD%98%E5%9C%A8")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("data", data)
            self.assertEqual(len(data["data"]), 0)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_search_by_keyword_upstream_error(self, mock_urlopen):
        """Route should return 502 when StockShark is unreachable."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.side_effect = Exception("Connection refused")

            resp = client.get("/api/search/by-keyword?keyword=test")
            self.assertEqual(resp.status_code, 502)
            data = resp.get_json()
            self.assertIn("error", data)
        finally:
            self._restore(mod, orig)


if __name__ == "__main__":
    unittest.main()
