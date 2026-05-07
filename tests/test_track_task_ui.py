# -*- coding: utf-8 -*-
"""Tests for track-task-ui: keywords proxy, task form mode, track badge."""

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


class _TrackTaskUITestBase(unittest.TestCase):
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


class TestKeywordsProxy(_TrackTaskUITestBase):
    """Task 1.1 & 1.2: GET /api/proxy/tracks/<id>/keywords proxies to agent."""

    @patch("app.urllib.request.urlopen")
    def test_keywords_proxy_returns_data(self, mock_urlopen):
        """Proxy should forward keywords response from data-agent."""
        client, mod, orig = self._get_client()
        try:
            resp_mock = MagicMock()
            resp_mock.status = 200
            resp_mock.read.return_value = json.dumps({
                "track_id": 3,
                "keywords": ["碳纤维", "复合材料", "石墨烯"],
                "count": 3
            }).encode()
            resp_mock.__enter__ = lambda s: s
            resp_mock.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = resp_mock

            resp = client.get("/api/proxy/tracks/3/keywords")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data["track_id"], 3)
            self.assertIn("碳纤维", data["keywords"])
            self.assertEqual(data["count"], 3)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_keywords_proxy_forwards_correct_url(self, mock_urlopen):
        """Proxy should call the agent API with the correct path."""
        client, mod, orig = self._get_client()
        try:
            resp_mock = MagicMock()
            resp_mock.status = 200
            resp_mock.read.return_value = json.dumps({
                "track_id": 5, "keywords": [], "count": 0
            }).encode()
            resp_mock.__enter__ = lambda s: s
            resp_mock.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = resp_mock

            client.get("/api/proxy/tracks/5/keywords")

            called_url = mock_urlopen.call_args[0][0]
            if isinstance(called_url, str):
                url_str = called_url
            else:
                url_str = getattr(called_url, "full_url", str(called_url))

            self.assertIn("/api/tracks/5/keywords", url_str,
                          f"Expected /api/tracks/5/keywords in URL, got {url_str}")
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_keywords_proxy_error_returns_502(self, mock_urlopen):
        """If agent is unreachable, proxy should return 502."""
        client, mod, orig = self._get_client()
        try:
            mock_urlopen.side_effect = Exception("Connection refused")

            resp = client.get("/api/proxy/tracks/99/keywords")
            self.assertEqual(resp.status_code, 502)
            data = resp.get_json()
            self.assertIn("error", data)
        finally:
            self._restore(mod, orig)


class TestTrackTaskListBadge(_TrackTaskUITestBase):
    """Task 4.1 & 4.2: Task list should display track badge with color."""

    @patch("app.urllib.request.urlopen")
    def test_task_list_proxy(self, mock_urlopen):
        """GET /api/tasks should return tasks from agent (proxy check)."""
        client, mod, orig = self._get_client()
        try:
            resp_mock = MagicMock()
            resp_mock.status = 200
            resp_mock.read.return_value = json.dumps([
                {"id": "t1", "subject": "新材料", "track_id": 3,
                 "sources": ["cailianshe"], "cron_expr": "0 */2 * * *",
                 "max_results": 20, "enabled": True},
                {"id": "t2", "subject": "核电", "track_id": None,
                 "sources": ["nbd"], "cron_expr": "0 9 * * *",
                 "max_results": 10, "enabled": True}
            ]).encode()
            resp_mock.__enter__ = lambda s: s
            resp_mock.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = resp_mock

            resp = client.get("/api/tasks")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["track_id"], 3)
            self.assertIsNone(data[1]["track_id"])
        finally:
            self._restore(mod, orig)


class TestCollectTaskSubmit(_TrackTaskUITestBase):
    """Task 3.1 & 3.2: Submit logic for track vs custom mode."""

    @patch("app.urllib.request.urlopen")
    def test_create_track_task_sends_track_id(self, mock_urlopen):
        """POST /api/tasks with track_id should forward to agent."""
        client, mod, orig = self._get_client()
        try:
            resp_mock = MagicMock()
            resp_mock.status = 200
            resp_mock.read.return_value = json.dumps({
                "id": "new1", "track_id": 3, "subject": "新材料",
                "cron_expr": "0 */2 * * *", "max_results": 20
            }).encode()
            resp_mock.__enter__ = lambda s: s
            resp_mock.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = resp_mock

            body = {
                "track_id": 3,
                "cron_expr": "0 */2 * * *",
                "max_results": 20
            }
            resp = client.post("/api/tasks",
                               data=json.dumps(body),
                               content_type="application/json")
            self.assertEqual(resp.status_code, 200)

            # Verify the forwarded request body
            call_args = mock_urlopen.call_args[0][0]
            sent_body = json.loads(call_args.data.decode())
            self.assertEqual(sent_body["track_id"], 3)
            self.assertNotIn("sources", sent_body)
        finally:
            self._restore(mod, orig)

    @patch("app.urllib.request.urlopen")
    def test_create_custom_task_sends_subject_sources(self, mock_urlopen):
        """POST /api/tasks without track_id should forward subject+sources."""
        client, mod, orig = self._get_client()
        try:
            resp_mock = MagicMock()
            resp_mock.status = 200
            resp_mock.read.return_value = json.dumps({
                "id": "new2", "subject": "核电",
                "sources": ["nbd", "36kr"],
                "cron_expr": "0 9 * * *", "max_results": 10
            }).encode()
            resp_mock.__enter__ = lambda s: s
            resp_mock.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = resp_mock

            body = {
                "subject": "核电",
                "sources": ["nbd", "36kr"],
                "cron_expr": "0 9 * * *",
                "max_results": 10
            }
            resp = client.post("/api/tasks",
                               data=json.dumps(body),
                               content_type="application/json")
            self.assertEqual(resp.status_code, 200)

            call_args = mock_urlopen.call_args[0][0]
            sent_body = json.loads(call_args.data.decode())
            self.assertEqual(sent_body["subject"], "核电")
            self.assertIn("nbd", sent_body["sources"])
            self.assertNotIn("track_id", sent_body)
        finally:
            self._restore(mod, orig)


class TestFrontendContainsTrackUI(unittest.TestCase):
    """Verify index.html contains all required track-task UI elements."""

    def setUp(self):
        tmpl_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates", "index.html"
        )
        with open(tmpl_path, encoding="utf-8") as f:
            self.html = f.read()

    def test_mode_toggle_buttons(self):
        """Task 2.1: Mode toggle (赛道 / 自定义) must exist."""
        self.assertIn("modeTrack", self.html)
        self.assertIn("modeCustom", self.html)
        self.assertIn("switchCollectMode", self.html)

    def test_track_section_with_dropdown(self):
        """Task 2.2: Track section with select dropdown must exist."""
        self.assertIn("trackSection", self.html)
        self.assertIn('id="mTrack"', self.html)

    def test_on_track_select_auto_fill(self):
        """Task 2.3: onTrackSelect function must auto-fill subject."""
        self.assertIn("onTrackSelect", self.html)
        self.assertIn("mSubject", self.html)

    def test_track_kw_area_with_scroll(self):
        """Task 2.4 & 2.5: Keywords area with max-height 120px + overflow-y auto."""
        self.assertIn("trackKwArea", self.html)
        # Check for max-height:120px and overflow-y:auto
        self.assertIn("max-height:120px", self.html)
        self.assertIn("overflow-y:auto", self.html)

    def test_switch_collect_mode_restores_editable(self):
        """Task 2.6: switchCollectMode restores subject/sources editable."""
        # In custom mode, pointerEvents should be restored
        self.assertIn("pointerEvents", self.html)
        self.assertIn("opacity", self.html)

    def test_track_mode_submit_without_sources(self):
        """Task 3.1: Track mode submit sends track_id, not sources."""
        self.assertIn("track_id:parseInt(trackId)", self.html)

    def test_custom_mode_submit_with_subject_sources(self):
        """Task 3.2: Custom mode submit sends subject + sources."""
        self.assertIn("subject,sources,cron_expr:cron,max_results:max", self.html)

    def test_edit_collect_form_track_mode(self):
        """Task 3.3: editCollectForm switches to track mode for track tasks."""
        self.assertIn("editCollectForm", self.html)
        self.assertIn("switchCollectMode('track')", self.html)

    def test_track_badge_in_task_list(self):
        """Task 4.1: Task list shows track badge with color."""
        self.assertIn("trackBadge", self.html)
        self.assertIn("trackMap", self.html)

    def test_track_color_mapping_from_api(self):
        """Task 4.2: Track map built from /api/proxy/tracks."""
        self.assertIn("_loadTracks", self.html)
        self.assertIn("trackMap[t.id]=t", self.html)


if __name__ == "__main__":
    unittest.main()
