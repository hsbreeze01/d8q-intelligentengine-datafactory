#!/usr/bin/env python3
"""v3 P0/P1 指标单测: _process_batch 分桶/非一字溢价/连板值/板块聚合."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sentiment


def D(m, d):
    return date(2026, m, d)


class FakeCur:
    """模拟真实 SQL 的 ORDER BY stock_code, date, id 排序."""
    def __init__(self, rows):
        self._rows = sorted(rows, key=lambda r: (r[1], r[0]))

    def execute(self, *a):
        pass

    def fetchall(self):
        return self._rows


# 5 股 x 4 天 (首日无 prev_close 不可判涨停, 连板链从 D2 起):
# 000001 银行: 10 -> 11(一字涨停) -> 12.1(一字涨停) -> 13.31(一字涨停, streak=3)
# 000002 银行: 10 -> 11(自然涨停) -> 11.5(+4.55) -> 12.0(+4.35)
# 000003 计算机: 10 -> 9(-10) -> 9.8(+8.89) -> 9.5(-3.06)
# 000004 银行: 10 -> 11(涨停) -> 12.1(涨停非一字) -> 11.0(-9.09 断板)
# 600001 未映射: 10 -> 10.5(+5) -> 9.5(-9.52) -> 9.0(-5.26)
ROWS = [
    (D(1, 5), "000001", 10.0, 10.0, 10.0, 1000.0, 0.0),
    (D(1, 5), "000002", 10.0, 10.0, 10.0, 1000.0, 0.0),
    (D(1, 5), "000003", 10.0, 10.0, 10.0, 1000.0, 0.0),
    (D(1, 5), "000004", 10.0, 10.0, 10.0, 1000.0, 0.0),
    (D(1, 5), "600001", 10.0, 10.0, 10.0, 1000.0, 0.0),
    (D(1, 6), "000001", 11.0, 11.0, 11.0, 2000.0, 10.0),    # 一字涨停
    (D(1, 6), "000002", 11.0, 11.2, 10.8, 2000.0, 10.0),    # 自然涨停
    (D(1, 6), "000003", 9.0, 9.2, 9.0, 500.0, -10.0),
    (D(1, 6), "000004", 11.0, 11.1, 10.9, 1200.0, 10.0),    # 自然涨停
    (D(1, 6), "600001", 10.5, 10.6, 10.4, 800.0, 5.0),
    (D(1, 7), "000001", 12.1, 12.1, 12.1, 3000.0, 10.0),    # 二连一字
    (D(1, 7), "000002", 11.5, 11.9, 11.3, 2500.0, 4.55),
    (D(1, 7), "000003", 9.8, 9.9, 9.7, 600.0, 8.89),
    (D(1, 7), "000004", 12.1, 12.2, 11.5, 1500.0, 10.0),    # 涨停, open 非一字
    (D(1, 7), "600001", 9.5, 9.6, 9.4, 900.0, -9.52),
    (D(1, 8), "000001", 13.31, 13.31, 13.31, 3500.0, 10.0),  # 三连一字
    (D(1, 8), "000002", 12.0, 12.1, 11.8, 2600.0, 4.35),
    (D(1, 8), "000003", 9.5, 9.7, 9.4, 700.0, -3.06),
    (D(1, 8), "000004", 11.0, 12.0, 10.9, 1600.0, -9.09),   # 断板大跌
    (D(1, 8), "600001", 9.0, 9.2, 8.9, 950.0, -5.26),
]

META = {"industry": {"000001": "银行", "000002": "银行",
                     "000003": "计算机", "000004": "银行"},
        "name": {"000001": "银行A", "000002": "银行B",
                 "000003": "软件C", "000004": "银行D"}}
DATE_IDX = {D(1, 5): 0, D(1, 6): 1, D(1, 7): 2, D(1, 8): 3}


def _approx(a, b, tol=0.02):
    assert a is not None and not (a != a), f"got NaN/None, expect {b}"
    assert abs(a - b) <= tol, f"{a} !~ {b}"


def test_process_batch_v3():
    cnt, lu, pm, pm2, sec, lead = sentiment._process_batch(
        FakeCur(ROWS), "000001", "999999", DATE_IDX, META)

    # --- 家数/涨跌 ---
    assert int(cnt.loc[D(1, 6), "limit_up"]) == 3
    assert int(cnt.loc[D(1, 6), "limit_down"]) == 1
    assert int(cnt.loc[D(1, 7), "limit_up"]) == 2
    assert int(cnt.loc[D(1, 8), "limit_up"]) == 1
    assert int(cnt.loc[D(1, 8), "up"]) == 2
    assert int(cnt.loc[D(1, 8), "down"]) == 3

    # --- 涨跌幅 21 档分桶(注意浮点精度: 涨停涨幅可能 10.000000000000009 落 b10) ---
    assert int(cnt.loc[D(1, 6), "b10"]) == 3      # 三只涨停
    assert int(cnt.loc[D(1, 6), "b5"]) == 1       # 600001 +5%
    assert int(cnt.loc[D(1, 6), "b-10"]) == 1     # 000003 -10%
    assert int(cnt.loc[D(1, 7), "b10"]) == 2
    assert int(cnt.loc[D(1, 7), "b4"]) == 1
    assert int(cnt.loc[D(1, 7), "b8"]) == 1
    assert int(cnt.loc[D(1, 8), "b10"]) == 1
    assert int(cnt.loc[D(1, 8), "b4"]) == 1
    assert int(cnt.loc[D(1, 8), "b-4"]) == 1
    assert int(cnt.loc[D(1, 8), "b-6"]) == 1
    assert int(cnt.loc[D(1, 8), "b-10"]) == 1
    # 各日桶总数 = 有效涨跌幅数
    for d in (D(1, 6), D(1, 7), D(1, 8)):
        tot = sum(int(cnt.loc[d, f"b{i}"]) for i in range(-10, 11))
        assert tot == int(cnt.loc[d, "pct_n"]), (d, tot)

    # --- 连板高度 ---
    assert int(lu[(lu["date"] == D(1, 8))]["streak"].max()) == 3

    # --- 昨涨停溢价 / 非一字溢价 ---
    # D7: 昨涨停(000001/000002/000004) 今 +10/+4.55/+10 -> mean 8.18 median 10
    g7 = pm[pm["date"] == D(1, 7)]["pct_chg"]
    _approx(g7.mean(), 8.18)
    _approx(float(g7.median()), 10.0)
    # D7 非一字(剔除 000001 一字): +4.55/+10 -> 7.27
    g7n = pm2[pm2["date"] == D(1, 7)]["pct_chg"]
    assert len(g7n) == 2
    _approx(g7n.mean(), 7.27)
    # D8: 昨涨停(000001/000004) 今 +10/-9.09 -> mean 0.45
    g8 = pm[pm["date"] == D(1, 8)]["pct_chg"]
    _approx(g8.mean(), 0.455)
    # D8 非一字: 剔除 000001 一字 -> 仅 -9.09
    g8n = pm2[pm2["date"] == D(1, 8)]["pct_chg"]
    assert len(g8n) == 1
    _approx(g8n.mean(), -9.09)

    # --- 连板值/连比值: D8 昨连板(000001 二板/000004 二板), 今 +10 / -9.09 ---
    assert int(cnt.loc[D(1, 7), "lb2"]) == 0       # D7 无昨 2 板以上
    assert int(cnt.loc[D(1, 8), "lb2"]) == 2
    assert int(cnt.loc[D(1, 8), "lb2s"]) == 1      # +10 >= 7 接力
    assert int(cnt.loc[D(1, 8), "lb2b"]) == 1      # -9.09 <= 0 断板
    _approx(cnt.loc[D(1, 8), "lb2s"] / cnt.loc[D(1, 8), "lb2"], 0.5)
    _approx(cnt.loc[D(1, 8), "lb2b"] / cnt.loc[D(1, 8), "lb2"], 0.5)

    # --- 板块聚合(申万一级) ---
    s7 = sec[sec["date"] == D(1, 7)]
    bank = s7[s7["industry"] == "银行"].iloc[0]
    assert int(bank["stock_count"]) == 3
    assert int(bank["up_count"]) == 3
    _approx(float(bank["turnover"]), 7000.0, 0.01)
    _approx(float(bank["pct_sum"]) / 3, 8.18)
    comp = s7[s7["industry"] == "计算机"].iloc[0]
    _approx(float(comp["turnover"]), 600.0, 0.01)
    # 龙头: D7 银行 max pct -> 000001(idxmax 首个)
    l7 = lead[lead["date"] == D(1, 7)]
    lb_bank = l7[l7["industry"] == "银行"].iloc[0]
    assert lb_bank["code"] == "000001"
    assert lb_bank["pct"] >= 9.99
    l8 = lead[lead["date"] == D(1, 8)]
    lb_bank8 = l8[l8["industry"] == "银行"].iloc[0]
    assert lb_bank8["code"] == "000001"
    # 未分类股(600001)归"未分类"
    unc = s7[s7["industry"] == "未分类"]
    assert len(unc) == 1

    print("test_process_batch_v3: ALL PASS")


if __name__ == "__main__":
    test_process_batch_v3()
