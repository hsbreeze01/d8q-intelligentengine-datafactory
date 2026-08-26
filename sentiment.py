#!/usr/bin/env python3
"""市场情绪温度计 —— 从 stock_data_daily 日线推导 A 股短线情绪指标。

口径(每交易日):
  limit_up / limit_down / touch_limit   涨停/跌停/盘中触涨停家数
      涨停价 = round(prev_close * (1+板块比例), 2); 30/68 开头 20%, 其余 10%
      仅当该股上一条记录为相邻市场交易日(停牌复牌不chain); ST(5%)与北交所(30%)不在库中, 天然排除
  seal_rate        封板率 = 收盘涨停 / 盘中触板
  max_streak       连板高度(连续收盘涨停天数, 跨停牌断档重置)
  streak_dist      连板梯队 JSON {"1":首板数,"2":二板数,"3":三板数,"4+":四板以上数}
  promo_1_2 / promo_2_3 / promo_3_up / promo_overall   晋级率(昨N板今继续涨停/昨N板)
  premium_mean / premium_median   昨日涨停股今日涨跌幅 均值/中位数(%)
  big_face         大面票数(昨涨停, 今跌幅<=-9.8%)
  heaven_hell      天地板数(今盘中触涨停, 收盘跌停)
  up_ratio         上涨家数占比
  total_turnover   全市场成交额(元)
  composite        情绪指数 0-100: 六子指标 [涨停家数.20 连板高度.15 连板率.20 封板率.15 昨涨停溢价.15 上涨占比.15]
                   各自 expanding 历史分位(min_periods=60, 无未来函数)加权合成
  phase            冰点(<20)/修复(<40)/温和(<60)/亢奋(<80)/过热(>=80)

用法:
  venv/bin/python sentiment.py --backfill    # 全量回填全部交易日
  venv/bin/python sentiment.py               # 重算近 30 交易日(每日增量, 幂等 REPLACE)
  venv/bin/python sentiment.py --days 90     # 重算近 90 交易日

内存策略: 按股票代码分批(range scan), 每批约 BATCH 只, 流式聚合, 峰值内存有界。
"""
import argparse
import json
import logging

import numpy as np
import pandas as pd
import pymysql

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("sentiment")

DB = {"host": "127.0.0.1", "port": 3306, "user": "root", "password": "password",
      "database": "stock_analysis_system", "charset": "utf8mb4"}

BATCH = 300

WEIGHTS = {
    "limit_up": 0.20,
    "max_streak": 0.15,
    "promo_overall": 0.20,
    "seal_rate": 0.15,
    "premium_mean": 0.15,
    "up_ratio": 0.15,
}
PHASES = [(0, "冰点"), (20, "修复"), (40, "温和"), (60, "亢奋"), (80, "过热")]


def _conn():
    return pymysql.connect(**DB)


def _fetch_codes(cur):
    cur.execute("SELECT DISTINCT stock_code FROM stock_data_daily ORDER BY stock_code")
    return [r[0] for r in cur.fetchall()]


def _fetch_dates(cur):
    cur.execute("SELECT DISTINCT date FROM stock_data_daily ORDER BY date")
    dates = [r[0] for r in cur.fetchall()]
    return dates, {d: i for i, d in enumerate(dates)}


def _process_batch(cur, code_lo, code_hi, date_idx):
    cur.execute(
        "SELECT date, stock_code, close, high, turnover, change_percentage "
        "FROM stock_data_daily WHERE stock_code >= %s AND stock_code < %s "
        "ORDER BY stock_code, date, id",
        (code_lo, code_hi))
    rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["date", "stock_code", "close", "high",
                                     "turnover", "change_percentage"])
    # 上游采集器存在重复插入(同一 stock-day 2~9 条副本), 去重取最早副本
    df = df.drop_duplicates(subset=["stock_code", "date"], keep="first")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["high"] = pd.to_numeric(df["high"], errors="coerce")
    df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
    df = df.dropna(subset=["close"]).reset_index(drop=True)

    df["didx"] = df["date"].map(date_idx)
    g = df.groupby("stock_code", sort=False)
    df["prev_close"] = g["close"].shift(1)
    df["prev_didx"] = g["didx"].shift(1)
    ok_prev = (df["prev_didx"] == df["didx"] - 1).values

    pre2 = df["stock_code"].str[:2]
    lim_pct = np.where(pre2.isin(["30", "68"]).values, 0.20, 0.10)
    up_lim = (df["prev_close"].values * (1 + lim_pct)).round(2)
    dn_lim = (df["prev_close"].values * (1 - lim_pct)).round(2)
    close_v, high_v = df["close"].values, df["high"].values
    is_lu = ok_prev & (close_v >= up_lim - 0.001)
    is_ld = ok_prev & (close_v <= dn_lim + 0.001)
    is_touch = ok_prev & (high_v >= up_lim - 0.001)

    codes = df["stock_code"].values
    streak = np.zeros(len(df), dtype=np.int16)
    run = 0
    for i in range(len(df)):
        if i > 0 and codes[i] != codes[i - 1]:
            run = 0
        run = run + 1 if is_lu[i] else 0
        streak[i] = run
    df["streak"] = streak
    df["prev_streak"] = g["streak"].shift(1)
    df["prev_lu"] = g["streak"].shift(1).ge(1)
    # 涨跌幅自算(close/prev_close-1), 不依赖采集器 change_percentage(副本间不一致)
    df["pct_chg"] = (df["close"] / df["prev_close"] - 1.0) * 100.0

    dv = df["date"].values
    cnt = pd.DataFrame({
        "date": dv,
        "total": 1,
        "limit_up": is_lu.astype(np.int8),
        "limit_down": is_ld.astype(np.int8),
        "touch_limit": is_touch.astype(np.int8),
        "up": (df["pct_chg"].values > 0).astype(np.int8),
        "turnover": df["turnover"].values,
        "p1": (df["prev_streak"] == 1).astype(np.int8),
        "p1x": ((df["prev_streak"] == 1) & is_lu).astype(np.int8),
        "p2": (df["prev_streak"] == 2).astype(np.int8),
        "p2x": ((df["prev_streak"] == 2) & is_lu).astype(np.int8),
        "p3": (df["prev_streak"] >= 3).astype(np.int8),
        "p3x": ((df["prev_streak"] >= 3) & is_lu).astype(np.int8),
        "pl": (df["prev_streak"] >= 1).astype(np.int8),
        "plx": ((df["prev_streak"] >= 1) & is_lu).astype(np.int8),
        "big_face": (df["prev_lu"] & (df["pct_chg"].values <= -9.8)).astype(np.int8),
        "heaven_hell": (is_touch & is_ld).astype(np.int8),
    }).groupby("date").sum()

    lu_rows = df[is_lu][["date", "streak"]]
    pm_rows = df[df["prev_lu"]][["date", "pct_chg"]]
    return cnt, lu_rows, pm_rows


def compute() -> pd.DataFrame:
    conn = _conn()
    cur = conn.cursor()
    codes = _fetch_codes(cur)
    dates, date_idx = _fetch_dates(cur)
    log.info("stocks=%d trading_days=%d", len(codes), len(dates))

    cnt_parts, lu_parts, pm_parts = [], [], []
    for i in range(0, len(codes), BATCH):
        lo, hi = codes[i], codes[i + BATCH] if i + BATCH < len(codes) else codes[-1] + "~"
        r = _process_batch(cur, lo, hi, date_idx)
        if r is not None:
            cnt, lu, pm = r
            cnt_parts.append(cnt)
            lu_parts.append(lu)
            pm_parts.append(pm)
        if (i // BATCH) % 5 == 0:
            log.info("batch %d/%d", i // BATCH + 1, (len(codes) + BATCH - 1) // BATCH)
    conn.close()

    cnt = pd.concat(cnt_parts).groupby("level_0" if False else "date").sum()
    base = pd.DataFrame(index=cnt.index)
    for c in ("total", "limit_up", "limit_down", "touch_limit", "up", "turnover",
              "p1", "p1x", "p2", "p2x", "p3", "p3x", "pl", "plx", "big_face", "heaven_hell"):
        base[c] = cnt[c]

    lu = pd.concat(lu_parts)
    stu = lu.groupby("date")["streak"]
    base["max_streak"] = stu.max()
    base["streak_dist"] = stu.agg(lambda x: json.dumps({
        "1": int((x == 1).sum()), "2": int((x == 2).sum()),
        "3": int((x == 3).sum()), "4+": int((x >= 4).sum())}))

    pm = pd.concat(pm_parts).groupby("date")["pct_chg"]
    base["premium_mean"] = pm.mean().round(3)
    base["premium_median"] = pm.median().round(3)

    base["total_turnover"] = base.pop("turnover")
    base["up_ratio"] = base.pop("up") / base["total"]
    base["seal_rate"] = base["limit_up"] / base["touch_limit"].replace(0, np.nan)
    base["promo_1_2"] = base.pop("p1x") / base.pop("p1").replace(0, np.nan)
    base["promo_2_3"] = base.pop("p2x") / base.pop("p2").replace(0, np.nan)
    base["promo_3_up"] = base.pop("p3x") / base.pop("p3").replace(0, np.nan)
    base["promo_overall"] = base.pop("plx") / base.pop("pl").replace(0, np.nan)

    def _epct(s):
        return pd.Series(s.values, index=s.index).expanding(min_periods=60).apply(
            lambda x: (x <= x[-1]).mean() * 100.0, raw=True)

    pct = pd.DataFrame({k: _epct(base[k]) for k in WEIGHTS})
    w_series = pd.Series(WEIGHTS)
    num = pct.mul(w_series, axis=1).sum(axis=1, skipna=True)
    den = pct.notna().mul(w_series, axis=1).sum(axis=1)
    base["composite"] = (num / den.replace(0, np.nan)).round(2)
    base["composite_ma5"] = base["composite"].rolling(5).mean().round(2)

    def _phase(v):
        if pd.isna(v):
            return None
        label = "冰点"
        for th, name in PHASES:
            if v >= th:
                label = name
        return label

    base["phase"] = base["composite"].map(_phase)
    base = base[base["limit_up"].notna()]
    return base.reset_index()


DDL = """
CREATE TABLE IF NOT EXISTS sentiment_daily (
  date DATE NOT NULL PRIMARY KEY,
  limit_up INT, limit_down INT, touch_limit INT,
  seal_rate DECIMAL(6,4),
  max_streak INT, streak_dist VARCHAR(64),
  promo_1_2 DECIMAL(6,4), promo_2_3 DECIMAL(6,4), promo_3_up DECIMAL(6,4),
  promo_overall DECIMAL(6,4),
  premium_mean DECIMAL(7,3), premium_median DECIMAL(7,3),
  big_face INT, heaven_hell INT,
  up_ratio DECIMAL(6,4), total_turnover DECIMAL(20,2),
  composite DECIMAL(6,2), composite_ma5 DECIMAL(6,2),
  phase VARCHAR(8),
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

COLS = ["date", "limit_up", "limit_down", "touch_limit", "seal_rate", "max_streak",
        "streak_dist", "promo_1_2", "promo_2_3", "promo_3_up", "promo_overall",
        "premium_mean", "premium_median", "big_face", "heaven_hell", "up_ratio",
        "total_turnover", "composite", "composite_ma5", "phase"]


def persist(base, tail_days):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(DDL)
    n = 0
    for r in base.tail(tail_days).to_dict("records"):
        row = [r["date"]] + [
            None if (r.get(c) is None or (isinstance(r.get(c), float) and np.isnan(r.get(c))))
            else r.get(c)
            for c in COLS[1:]]
        cur.execute(
            "REPLACE INTO sentiment_daily ({}) VALUES ({})".format(
                ",".join(COLS), ",".join(["%s"] * len(COLS))),
            row)
        n += 1
    conn.commit()
    conn.close()
    log.info("persisted %d days (tail=%d, computed=%d)", n, tail_days, len(base))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true", help="回填全部交易日")
    ap.add_argument("--days", type=int, default=30, help="重算近 N 交易日(默认30)")
    args = ap.parse_args()
    base = compute()
    tail = len(base) if args.backfill else args.days
    persist(base, tail)
    last = base.iloc[-1]
    log.info("latest %s composite=%s phase=%s lu=%d ld=%d max_streak=%s",
             last["date"], last["composite"], last["phase"],
             int(last["limit_up"]), int(last["limit_down"]), last["max_streak"])


if __name__ == "__main__":
    main()
