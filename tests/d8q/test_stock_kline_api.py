import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'src'))

import app as app_module  # noqa: E402


def _rows_desc():
    # 模拟 DB 游标返回（date DESC）：09-02 在前、09-01 在后
    return [
        (datetime.date(2026, 9, 2), 48.63, 48.00, 49.04, 47.43, 57704),
        (datetime.date(2026, 9, 1), 47.80, 45.98, 47.89, 45.87, 48192),
    ]


def test_rows_desc_become_chronological():
    bars = app_module._kline_rows_to_bars(_rows_desc())
    assert [b['date'] for b in bars] == ['2026-09-01', '2026-09-02']


def test_bar_fields_and_types():
    b = app_module._kline_rows_to_bars(_rows_desc())[0]
    assert b['date'] == '2026-09-01'
    assert b['open'] == 47.8 and b['close'] == 45.98
    assert b['high'] == 47.89 and b['low'] == 45.87
    assert b['volume'] == 48192
    assert isinstance(b['open'], float) and isinstance(b['volume'], int)


def test_empty_rows():
    assert app_module._kline_rows_to_bars([]) == []


def test_kline_route_registered_as_get():
    rules = {r.rule: r for r in app_module.app.url_map.iter_rules()}
    assert '/api/stock/kline' in rules
    assert 'GET' in rules['/api/stock/kline'].methods
