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


if __name__ == "__main__":
    unittest.main()
