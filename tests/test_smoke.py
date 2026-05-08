# -*- coding: utf-8 -*-
"""Smoke test – ensures the test suite always has at least one passing test."""
import pytest


def test_smoke():
    """Project test infrastructure is working."""
    assert True


class TestStockDetailRoute:
    """Test Flask route /stock/<code> serves the SPA shell."""

    @pytest.fixture()
    def client(self):
        import app as _app
        _app.app.config["TESTING"] = True
        with _app.app.test_client() as c:
            # Stub session so auth passes
            with c.session_transaction() as sess:
                sess["username"] = "test"
                sess["role"] = "admin"
            yield c

    def test_stock_detail_returns_200(self, client):
        resp = client.get("/stock/600733")
        assert resp.status_code == 200

    def test_stock_detail_returns_html(self, client):
        resp = client.get("/stock/600733")
        content_type = resp.content_type or ""
        assert "text/html" in content_type

    def test_stock_detail_contains_spa_shell(self, client):
        resp = client.get("/stock/600733")
        data = resp.data.decode("utf-8")
        assert "D8Q" in data
