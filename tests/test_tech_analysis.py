# -*- coding: utf-8 -*-
"""Tests for stock-technical-analysis: calc functions, chart renderers, signals, UI."""

import os
import unittest

TMPL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates", "index.html",
)


def _read_html():
    with open(TMPL, encoding="utf-8") as f:
        return f.read()


# ── Task 1.1: calcMA / calcEMA ──────────────────────────────────────────────

class TestCalcMACalcEMA(unittest.TestCase):
    """Task 1.1: calcMA(closes, periods) and calcEMA(closes, period) must exist."""

    def setUp(self):
        self.html = _read_html()

    def test_calcma_exists(self):
        self.assertIn("function calcMA(", self.html)

    def test_calcma_accepts_periods(self):
        self.assertIn("periods", self.html)

    def test_calcema_exists(self):
        self.assertIn("function calcEMA(", self.html)


# ── Task 1.2: calcMACD ──────────────────────────────────────────────────────

class TestCalcMACD(unittest.TestCase):
    """Task 1.2: calcMACD(closes, short, long, signal) must exist and return dif/dea/macd."""

    def setUp(self):
        self.html = _read_html()

    def test_calcmacd_exists(self):
        self.assertIn("function calcMACD(", self.html)

    def test_calcmacd_returns_dif_dea_macd(self):
        self.assertIn("dif: dif, dea: dea, macd: macd", self.html)

    def test_calcmacd_uses_calcema(self):
        self.assertIn("calcEMA(dif,", self.html)


# ── Task 1.3: calcKDJ ───────────────────────────────────────────────────────

class TestCalcKDJ(unittest.TestCase):
    """Task 1.3: calcKDJ(highs, lows, closes, n, m1, m2) must exist and return k/d/j."""

    def setUp(self):
        self.html = _read_html()

    def test_calckdj_exists(self):
        self.assertIn("function calcKDJ(", self.html)

    def test_calckdj_accepts_highs_lows(self):
        self.assertIn("highs, lows, closes", self.html)

    def test_calckdj_returns_k_d_j(self):
        self.assertIn("k: K, d: D, j: J", self.html)


# ── Task 1.4: calcBOLL ──────────────────────────────────────────────────────

class TestCalcBOLL(unittest.TestCase):
    """Task 1.4: calcBOLL(closes, n, k) must exist and return upper/mid/lower."""

    def setUp(self):
        self.html = _read_html()

    def test_calcboll_exists(self):
        self.assertIn("function calcBOLL(", self.html)

    def test_calcboll_returns_upper_mid_lower(self):
        self.assertIn("upper: upper, mid: mid, lower: lower", self.html)

    def test_calcboll_uses_std(self):
        self.assertIn("Math.sqrt(sqSum", self.html)


# ── Task 1.5: calcRSI ───────────────────────────────────────────────────────


class TestCalcRSI(unittest.TestCase):
    """Task 1.5: calcRSI(closes, periods) must exist and return per-period arrays."""

    def setUp(self):
        self.html = _read_html()

    def test_calcrsi_exists(self):
        self.assertIn("function calcRSI(", self.html)

    def test_calcrsi_accepts_periods(self):
        self.assertIn("periods = periods || [6, 12, 24]", self.html)

    def test_calcrsi_uses_rsi_formula(self):
        self.assertIn("100 - 100 / (1 + avgGain / avgLoss)", self.html)

    def test_calcrsi_returns_per_period(self):
        self.assertIn("result[p] = arr", self.html)


# ── Task 2.1-2.5: ECharts indicator chart drawing ──────────────────────────


class TestDrawTechCharts(unittest.TestCase):
    """Tasks 2.1-2.5: drawTechChart handles MA/MACD/KDJ/BOLL/RSI."""

    def setUp(self):
        self.html = _read_html()

    def test_draw_tech_chart_exists(self):
        self.assertIn("function drawTechChart(type)", self.html)

    def test_ma_chart_branch(self):
        self.assertIn("type==='ma'", self.html)

    def test_ma_uses_calcMA(self):
        # MA branch calls calcMA
        self.assertIn("calcMA(closes,5)", self.html)
        self.assertIn("calcMA(closes,10)", self.html)
        self.assertIn("calcMA(closes,20)", self.html)

    def test_macd_chart_branch(self):
        self.assertIn("type==='macd'", self.html)

    def test_macd_draws_dif_dea_bar(self):
        self.assertIn("name:'DIF',type:'line'", self.html)
        self.assertIn("name:'DEA',type:'line'", self.html)
        self.assertIn("name:'MACD',type:'bar'", self.html)

    def test_kdj_chart_branch(self):
        self.assertIn("type==='kdj'", self.html)

    def test_kdj_draws_k_d_j(self):
        self.assertIn("name:'K',type:'line'", self.html)
        self.assertIn("name:'D',type:'line'", self.html)
        self.assertIn("name:'J',type:'line'", self.html)

    def test_boll_chart_branch(self):
        self.assertIn("type==='boll'", self.html)

    def test_boll_draws_bands(self):
        self.assertIn("name:'\u4e0a\u8f68'", self.html)  # 上轨
        self.assertIn("name:'\u4e2d\u8f68'", self.html)  # 中轨
        self.assertIn("name:'\u4e0b\u8f68'", self.html)  # 下轨

    def test_rsi_chart_branch(self):
        self.assertIn("type==='rsi'", self.html)

    def test_rsi_draws_multi_period(self):
        self.assertIn("name:'RSI6'", self.html)
        self.assertIn("name:'RSI12'", self.html)
        self.assertIn("name:'RSI24'", self.html)


# ── Task 3.1-3.3: Signal evaluation and verdict ────────────────────────────


class TestEvalSignals(unittest.TestCase):
    """Tasks 3.1-3.3: evalTechSignals computes signals and renders verdict."""

    def setUp(self):
        self.html = _read_html()

    def test_eval_signals_exists(self):
        self.assertIn("function evalTechSignals(", self.html)

    def test_evaluates_ma_signal(self):
        # MA signal: checks ma5/ma10/ma20 alignment
        self.assertIn("name:'MA'", self.html)

    def test_evaluates_macd_signal(self):
        self.assertIn("name:'MACD'", self.html)

    def test_evaluates_kdj_signal(self):
        self.assertIn("name:'KDJ'", self.html)

    def test_evaluates_rsi_signal(self):
        self.assertIn("name:'RSI'", self.html)

    def test_evaluates_boll_signal(self):
        self.assertIn("name:'BOLL'", self.html)

    def test_signal_types(self):
        # buy/sell/neutral signals
        self.assertIn("sig:'buy'", self.html)
        self.assertIn("sig:'sell'", self.html)
        self.assertIn("sig:'neutral'", self.html)

    def test_signal_panel_render(self):
        # Renders into techSignals container
        self.assertIn("getElementById('techSignals')", self.html)

    def test_verdict_render(self):
        # Renders into techVerdict container
        self.assertIn("getElementById('techVerdict')", self.html)

    def test_verdict_logic(self):
        # Counts buy/sell to determine verdict
        self.assertIn("signals.filter(s=>s.sig==='buy').length", self.html)
        self.assertIn("signals.filter(s=>s.sig==='sell').length", self.html)


# ── Task 4.1-4.3: switchSDTab('tech') panel integration ────────────────────


class TestSDTechPanel(unittest.TestCase):
    """Tasks 4.1-4.3: loadSDTech renders panel with toolbar, chart, signals."""

    def setUp(self):
        self.html = _read_html()

    def test_load_sd_tech_exists(self):
        self.assertIn("function loadSDTech(", self.html)

    def test_switch_tab_routes_to_tech(self):
        self.assertIn("case 'tech':loadSDTech(c)", self.html)

    def test_tech_toolbar_buttons(self):
        # Toolbar buttons trigger drawTechChart for each indicator type
        # onclick uses escaped quotes inside JS string: drawTechChart(\\'ma\\')
        self.assertIn("drawTechChart(\\'ma\\')", self.html)
        self.assertIn("drawTechChart(\\'macd\\')", self.html)
        self.assertIn("drawTechChart(\\'kdj\\')", self.html)
        self.assertIn("drawTechChart(\\'boll\\')", self.html)
        self.assertIn("drawTechChart(\\'rsi\\')", self.html)

    def test_tech_chart_container(self):
        self.assertIn("id=\"techChart\"", self.html)

    def test_signals_container(self):
        self.assertIn("id=\"techSignals\"", self.html)

    def test_verdict_container(self):
        self.assertIn("id=\"techVerdict\"", self.html)

    def test_tech_default_chart_is_ma(self):
        self.assertIn("drawTechChart('ma')", self.html)

    def test_tech_fetches_kline_data(self):
        self.assertIn("/api/stock/kline?", self.html)


# ── Task 5.1: Inline CSS styles ─────────────────────────────────────────────


class TestTechStyles(unittest.TestCase):
    """Task 5.1: Technical analysis panel has inline CSS."""

    def setUp(self):
        self.html = _read_html()

    def test_stock_tabs_style(self):
        self.assertIn(".stock-tabs{", self.html)

    def test_stock_tab_style(self):
        self.assertIn(".stock-tab{", self.html)

    def test_chart_container_height(self):
        self.assertIn("height:300px", self.html)


if __name__ == "__main__":
    unittest.main()
