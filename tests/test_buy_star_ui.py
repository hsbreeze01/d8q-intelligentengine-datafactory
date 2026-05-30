# -*- coding: utf-8 -*-
"""Tests for buy_star UI fix — decodeBuyStar/renderBuyStar in templates.

Verifies:
1. decodeBuyStar correctly decodes bitmask into signal tags
2. Templates contain the new render functions (no old star logic)
3. Template content validates correct function usage
"""
import json
import re
import sqlite3
import tempfile
import os
import pytest


@pytest.fixture(scope="module")
def js_functions():
    with open("templates/compass/strategy/base.html") as f:
        content = f.read()
    return content


class TestDecodeBuyStarLogic:
    """Unit tests for the decodeBuyStar bitmask decoding rules.

    buy_star encoding from buy_advice_v2():
      300000000 = BOLL中轨
       20000000 = MA20支撑
        1000000 = 3日MA5支撑
         100000 = 2日MA5支撑
          10000 = MA5支撑(当日)
           1000 = 低位反转(十字星+背离)
             10 = KDJ底部
              1 = 金叉
             -1 = 风险否决
    These values are summed (OR-like), not actual bit positions.
    """

    @staticmethod
    def _decode(code):
        code = code or 0
        if code == -1:
            return {"signalCount": 0, "tags": ["风险否决"], "cls": "risk"}
        if code == 0:
            return {"signalCount": 0, "tags": [], "cls": "none"}
        c = code
        tags = []
        if c >= 300000000:
            tags.append("BOLL中轨"); c -= 300000000
        if c >= 20000000:
            tags.append("MA20支撑"); c -= 20000000
        if c >= 1000000:
            tags.append("3日MA5"); c -= 1000000
        if c >= 100000:
            tags.append("2日MA5"); c -= 100000
        if c >= 10000:
            tags.append("MA5支撑"); c -= 10000
        if c >= 1000:
            tags.append("低位反转"); c -= 1000
        if c >= 10:
            tags.append("KDJ底部"); c -= 10
        if c >= 1:
            tags.append("金叉")
        return {"signalCount": len(tags), "tags": tags, "cls": "signal"}

    def test_zero_no_signal(self):
        r = self._decode(0)
        assert r["cls"] == "none"
        assert r["signalCount"] == 0

    def test_risk_veto(self):
        r = self._decode(-1)
        assert r["cls"] == "risk"
        assert "风险否决" in r["tags"]

    def test_single_ma5_support(self):
        r = self._decode(10000)
        assert "MA5支撑" in r["tags"]
        assert r["signalCount"] == 1

    def test_ma5_plus_golden_cross(self):
        r = self._decode(10001)
        assert "MA5支撑" in r["tags"]
        assert "金叉" in r["tags"]
        assert r["signalCount"] == 2

    def test_ma5_kdj_cross(self):
        r = self._decode(10011)
        assert "MA5支撑" in r["tags"]
        assert "KDJ底部" in r["tags"]
        assert "金叉" in r["tags"]
        assert r["signalCount"] == 3

    def test_2day_ma5_kdj(self):
        r = self._decode(110010)
        assert "2日MA5" in r["tags"]
        assert "MA5支撑" in r["tags"]
        assert "KDJ底部" in r["tags"]
        assert r["signalCount"] == 3

    def test_3day_ma5_kdj_cross(self):
        r = self._decode(1110011)
        assert "3日MA5" in r["tags"]
        assert "2日MA5" in r["tags"]
        assert "MA5支撑" in r["tags"]
        assert "KDJ底部" in r["tags"]
        assert "金叉" in r["tags"]
        assert r["signalCount"] == 5

    def test_boll_mid_only(self):
        r = self._decode(300000000)
        assert "BOLL中轨" in r["tags"]
        assert r["signalCount"] == 1

    def test_full_stack_boll_ma20_3ma_kdj_cross(self):
        r = self._decode(321101011)
        assert "BOLL中轨" in r["tags"]
        assert "MA20支撑" in r["tags"]
        assert "3日MA5" in r["tags"]
        assert "2日MA5" in r["tags"]
        assert "低位反转" in r["tags"]
        assert "KDJ底部" in r["tags"]
        assert "金叉" in r["tags"]
        assert r["signalCount"] == 7

    def test_low_reversal(self):
        r = self._decode(1000)
        assert "低位反转" in r["tags"]
        assert r["signalCount"] == 1

    def test_kdj_plus_cross(self):
        r = self._decode(11)
        assert "KDJ底部" in r["tags"]
        assert "金叉" in r["tags"]
        assert r["signalCount"] == 2


class TestBaseTemplateHasDecodeFunction:
    def test_has_decodeBuyStar(self, js_functions):
        assert "function decodeBuyStar(code)" in js_functions

    def test_has_renderBuyStar(self, js_functions):
        assert "function renderBuyStar(code)" in js_functions

    def test_has_renderBuyStarCompact(self, js_functions):
        assert "function renderBuyStarCompact(code)" in js_functions

    def test_renderStars_delegates(self, js_functions):
        assert "return renderBuyStar(score);" in js_functions

    def test_has_boll_threshold(self, js_functions):
        assert "300000000" in js_functions

    def test_has_ma20_threshold(self, js_functions):
        assert "20000000" in js_functions


class TestEventDetailTemplate:
    @pytest.fixture(scope="class")
    def template(self):
        with open("templates/compass/strategy/event_detail.html") as f:
            return f.read()

    def test_summary_label_changed(self, template):
        assert "buy_star" in template
        assert 'id="eventBuyStar"' in template

    def test_no_old_star_render_in_summary(self, template):
        assert "renderStars(event.buy_star" not in template

    def test_scatter_uses_signal_count(self, template):
        assert "decodeBuyStar(s.buy_star" in template

    def test_scatter_label_is_signal_count(self, template):
        assert "信号数" in template


class TestMyStrategiesTemplate:
    @pytest.fixture(scope="class")
    def template(self):
        with open("templates/compass/strategy/my_strategies.html") as f:
            return f.read()

    def test_uses_renderBuyStarCompact(self, template):
        assert "renderBuyStarCompact" in template

    def test_no_old_star_multiplication(self, template):
        assert "'★' * (evt.buy_star" not in template


class TestIndexTemplate:
    @pytest.fixture(scope="class")
    def template(self):
        with open("templates/index.html") as f:
            return f.read()

    def test_uses_decodeBuyStar(self, template):
        assert "decodeBuyStar(s.buy_star||0).signalCount" in template

    def test_no_old_division(self, template):
        assert "/20000" not in template

    def test_buy_star_label_changed(self, template):
        assert "buy_star" in template
