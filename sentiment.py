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
  --- v2 补充指标(sentiment_extras_daily 表, AKShare EOD 采集, --collect-extras) ---
  lhb_count / lhb_net_buy / lhb_inst_seats   龙虎榜家数 / 净买合计(万) / 机构席位次数(东财, 区间可回填)
  margin_balance / margin_buy_amt            沪深融资余额 / 买入额(亿, 沪+深两源齐全才写, T+1 公布)
  broken_count                               炸板池家数(盘中触涨停未封住, 仅近 ~30 交易日可得)
  true_seal_rate                             真实封板率 = 收盘涨停/(收盘涨停+炸板) —— 修正日线 proxy 低估
  composite_v2 / phase_v2                    v2 合成: v1 六指标重加权 + 龙虎榜净买.15 + 真实封板率.10 + 融资余额.05
                                             缺失子指标按可用权重归一; extras 全缺时退化为 composite
  (北向净买额 2024-08-18 起港交所停发日度披露, 不采集)
  --- v3 P0/P1 指标(纯 DB 推导, 对标冰川每日图, 2026-08-27) ---
  --- v4 资金结构指标(龙虎榜机构席位口径, 对标冰川资金图, 2026-08-27) ---
  masculinity_score / retail_ratio  猛男值/菜比值(机构席位净买额占比, 0-100, 反向指标)
  phase_glae  冰川6级温度计(沸点/过热/微热/微冷/过冷/冰点, 基于 composite_v2)
  chg_dist        涨跌幅分布 JSON 21档(桶i覆盖[i,i+1)pp, clip ±10) —— 冰川图1柱状图
  up_count / down_count / flat_count   阳/阴/平家数
  mkt_chg_mean / mkt_chg_median        全市场平均涨幅 / 中位数(直方图插值近似)
  premium_mean_noyizi / _median_noyizi 昨涨停溢价剔除今日一字开盘(区分自然接力 vs 一字躺赢)
  lb_strength     连板值 = 昨连板(>=2板)股今涨幅>=7%比例(宽松接力口径, 冰川图5)
  lb_break        连比值 = 昨连板股今涨幅<=0比例(断板收平/跌, 韧性反向指标)
  sentiment_sector_daily 表: 申万一级行业日频聚合(成交额/家数/涨家数/均涨幅/龙头股)

用法:
  venv/bin/python sentiment.py --backfill    # 全量回填全部交易日
  venv/bin/python sentiment.py               # 重算近 30 交易日(每日增量, 幂等 REPLACE)
  venv/bin/python sentiment.py --days 90     # 重算近 90 交易日
  venv/bin/python sentiment.py --collect-extras          # 采集补充指标(近30日缺口)后计算
  venv/bin/python sentiment.py --collect-extras --extras-backfill   # 补充指标全量回填+全量计算
  venv/bin/python sentiment.py --collect-extras --only lhb   # 只采集单组(lhb|margin|broken)修复, 不计算

内存策略: 按股票代码分批(range scan), 每批约 BATCH 只, 流式聚合, 峰值内存有界。
"""
import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
import pymysql

try:
    import akshare as ak   # 仅 --collect-extras 需要; 缺失不影响纯 DB 计算
except ImportError:
    ak = None

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

WEIGHTS_V2 = {
    # v1 六指标等比缩放 0.70(保证 extras 全缺时 composite_v2 与 composite 数值一致),
    # 余 0.30 给补充指标: 龙虎榜净买强度 .15 / 真实封板率 .10 / 融资余额 .05
    "limit_up": 0.140,
    "promo_overall": 0.140,
    "max_streak": 0.105,
    "seal_rate": 0.105,
    "premium_mean": 0.105,
    "up_ratio": 0.105,
    "lhb_ratio": 0.15,          # 方案A: lhb 净买额/总成交额*1e4 (bp), rolling(252)分位, 剔除成交额扩张趋势
    "true_seal_rate": 0.10,
    "margin_balance": 0.05,
}

# A2: 冰川6级温度计专用权重(对标冰川每日图, 其本质是涨停/连板/封板结构, 不含龙虎榜/融资资金项).
# v1 六指标原比例 + true_seal_rate 0.15, 剩余项按当日权重归一. (2026-08-28 剔除 margin_balance, 名实对齐"纯结构")
WEIGHTS_GLAE = {
    "limit_up": 0.200,
    "promo_overall": 0.200,
    "max_streak": 0.150,
    "seal_rate": 0.150,
    "premium_mean": 0.150,
    "up_ratio": 0.150,
    "true_seal_rate": 0.15,
}

# --- v2 补充指标(采集参数) ---
EXTRAS_FROM = "2024-01-02"          # 与 stock_data_daily 起点一致
EXTRAS_SLEEP = 0.35                 # 逐日接口限频间隔(秒)
EXTRAS_RETRY = 3
EXTRA_COLS = ["lhb_count", "lhb_net_buy", "lhb_inst_seats", "lhb_inst_net_buy", "lhb_inst_buy", "lhb_total_buy",
              "margin_balance", "margin_buy_amt", "broken_count"]


def _conn():
    return pymysql.connect(**DB)


ROLLING_PCT_WINDOW = 252          # 方案A: 1 年约 252 交易日滚动, 丢弃远期低基数
ROLLING_PCT_MIN = 60                     # 与 expanding 最小样本一致, 早期稳定后再给分位


def _epct(s, use_rolling=False):
    """历史分位(无未来函数). 默认 expanding; use_rolling=True 走 rolling(252)
    对应方案 A: 对有量纲绝对值项(龙虎榜/融资)用 rolling 丢弃远期低基数样本, 抑制定向趋势失真.
    方案 B1: 稀疏序列(如 true_seal_rate 早期缺失)在首次非空前保持 NaN, 从有值起点开始算分位,
    避免整条序列因 leading NaN 全空.
    """
    arr = np.asarray(s.values, dtype=float)
    idx = s.index
    # Locate first non-NA: leading NA stays NA
    first_valid = next((i for i, v in enumerate(arr) if not np.isnan(v)), len(arr))
    if first_valid >= len(arr):
        return pd.Series(np.nan, index=idx)
    # Work on tail starting at first_valid
    tail = arr[first_valid:]
    ser = pd.Series(tail)
    # raw=True -> x is numpy 1D array (faster, no pandas overhead)
    if use_rolling:
        r = ser.rolling(ROLLING_PCT_WINDOW, min_periods=ROLLING_PCT_MIN)
        pct_tail = r.apply(lambda x: (x <= x[-1]).mean() * 100.0, raw=True).values
    else:
        pct_tail = ser.expanding(min_periods=ROLLING_PCT_MIN).apply(
            lambda x: (x <= x[-1]).mean() * 100.0, raw=True).values
    result = np.full(len(arr), np.nan, dtype=float)
    result[first_valid:] = pct_tail
    return pd.Series(result, index=idx)


# 方案 A: 这些分项天然有量纲/随市场规模扩张 -> 强制 rolling 分位
ROLLING_PCT_KEYS = {"lhb_ratio", "margin_balance"}


def _phase_label(v):
    if pd.isna(v):
        return None
    label = "冰点"
    for th, name in PHASES:
        if v >= th:
            label = name
    return label


def _phase_glae_label(v):
    """冰川6级温度计: 沸点>=90 / 过热>=80 / 微热>=60 / 微冷>=40 / 过冷>=20 / 冰点<20"""
    if pd.isna(v):
        return None
    if v >= 90:
        return "沸点"
    if v >= 80:
        return "过热"
    if v >= 60:
        return "微热"
    if v >= 40:
        return "微冷"
    if v >= 20:
        return "过冷"
    return "冰点"


def _fetch_codes(cur):
    cur.execute("SELECT DISTINCT stock_code FROM stock_data_daily ORDER BY stock_code")
    return [r[0] for r in cur.fetchall()]


def _fetch_dates(cur):
    cur.execute("SELECT DISTINCT date FROM stock_data_daily ORDER BY date")
    dates = [r[0] for r in cur.fetchall()]
    return dates, {d: i for i, d in enumerate(dates)}


def _process_batch(cur, code_lo, code_hi, date_idx, meta):
    cur.execute(
        "SELECT date, stock_code, close, high, open, turnover, change_percentage "
        "FROM stock_data_daily WHERE stock_code >= %s AND stock_code < %s "
        "ORDER BY stock_code, date, id",
        (code_lo, code_hi))
    rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["date", "stock_code", "close", "high",
                                     "open", "turnover", "change_percentage"])
    # 上游采集器存在重复插入(同一 stock-day 2~9 条副本), 去重取最早副本
    df = df.drop_duplicates(subset=["stock_code", "date"], keep="first")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["high"] = pd.to_numeric(df["high"], errors="coerce")
    df["open"] = pd.to_numeric(df["open"], errors="coerce")
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
    pctv = df["pct_chg"].values
    valid = ~np.isnan(pctv)
    psv = df["prev_streak"].fillna(0).values
    lb2 = (psv >= 2) & valid                    # 昨日连板(>=2板)基数
    # 一字开盘: 今开>=涨停价(含一字板); 非一字版溢价排除这些
    noyizi = df["prev_lu"].values & (df["open"].values < up_lim - 0.001)

    # 涨跌幅 21 档分桶(round 2dp 消除浮点尾差后 floor, clip 到 [-10,10], 桶 i 覆盖 [i, i+1))
    # 涨停股 close/prev-1 常为 9.9999999999986% 之类, 不 round 会散落 b9/b10
    clipped = np.clip(np.floor(np.round(pctv, 2)), -10, 10)

    cnt = pd.DataFrame({
        "date": dv,
        "total": 1,
        "limit_up": is_lu.astype(np.int8),
        "limit_down": is_ld.astype(np.int8),
        "touch_limit": is_touch.astype(np.int8),
        "up": (pctv > 0).astype(np.int8),
        "down": (valid & (pctv < 0)).astype(np.int8),
        "flat": (valid & (pctv == 0)).astype(np.int8),
        "pct_sum": np.where(valid, pctv, 0.0),
        "pct_n": valid.astype(np.int8),
        "turnover": df["turnover"].values,
        "p1": (df["prev_streak"] == 1).astype(np.int8),
        "p1x": ((df["prev_streak"] == 1) & is_lu).astype(np.int8),
        "p2": (df["prev_streak"] == 2).astype(np.int8),
        "p2x": ((df["prev_streak"] == 2) & is_lu).astype(np.int8),
        "p3": (df["prev_streak"] >= 3).astype(np.int8),
        "p3x": ((df["prev_streak"] >= 3) & is_lu).astype(np.int8),
        "pl": (df["prev_streak"] >= 1).astype(np.int8),
        "plx": ((df["prev_streak"] >= 1) & is_lu).astype(np.int8),
        "lb2": lb2.astype(np.int8),
        "lb2s": (lb2 & (pctv >= 7)).astype(np.int8),     # 连板值分子: 接力>=7%
        "lb2b": (lb2 & (pctv <= 0)).astype(np.int8),     # 连比值分子: 断板收平/跌
        "big_face": (df["prev_lu"] & (pctv <= -9.8)).astype(np.int8),
        "heaven_hell": (is_touch & is_ld).astype(np.int8),
        **{f"b{i}": ((clipped == i) & valid).astype(np.int8)
           for i in range(-10, 11)},
    }).groupby("date").sum()

    lu_rows = df[is_lu][["date", "streak"]]
    pm_rows = df[df["prev_lu"]][["date", "pct_chg"]]
    pm2_rows = df[noyizi][["date", "pct_chg"]]

    # 板块(申万一级)聚合: 成交额/家数/涨家数/均涨幅 + 批内龙头候选
    ind = df["stock_code"].map(meta["industry"]).fillna("未分类").values
    sdf = pd.DataFrame({
        "date": dv, "industry": ind,
        "turnover": df["turnover"].values,
        "up": (pctv > 0).astype(np.int8),
        "pct": np.where(valid, pctv, np.nan),
        "code": df["stock_code"].values})
    sdf = sdf[valid & ~np.isnan(df["turnover"].values)]
    sec = sdf.groupby(["date", "industry"], as_index=False).agg(
        turnover=("turnover", "sum"), stock_count=("pct", "count"),
        up_count=("up", "sum"), pct_sum=("pct", "sum"),
        best_i=("pct", "idxmax"))
    lead = sdf.loc[sdf.index.isin(sec["best_i"].values),
                   ["date", "industry", "code", "pct"]]
    return cnt, lu_rows, pm_rows, pm2_rows, sec, lead


def _fetch_meta(cur):
    """stock_basic -> {code: 申万一级行业}, {code: 股票名}; 缺失归'未分类'."""
    try:
        cur.execute("SELECT code, name, industry FROM stock_basic")
        rows = cur.fetchall()
    except pymysql.err.ProgrammingError:
        rows = []
    industry, name = {}, {}
    for code, nm, ind_ in rows:
        code = (code or "").strip()
        if not code:
            continue
        ind_ = (ind_ or "").strip()
        industry[code] = ind_.split("-")[0].strip() if ind_ else "未分类"
        name[code] = (nm or "").replace(" ", "")
    return {"industry": industry, "name": name}


# compute() 的板块聚合结果(供 persist_sectors 消费)
_SECTOR_DF = None


def compute():
    conn = _conn()
    cur = conn.cursor()
    codes = _fetch_codes(cur)
    dates, date_idx = _fetch_dates(cur)
    extras = _load_extras(cur)
    meta = _fetch_meta(cur)
    log.info("stocks=%d trading_days=%d extras_days=%d",
             len(codes), len(dates), 0 if extras is None else len(extras))

    cnt_parts, lu_parts, pm_parts, pm2_parts, sec_parts, lead_parts = \
        [], [], [], [], [], []
    for i in range(0, len(codes), BATCH):
        lo, hi = codes[i], codes[i + BATCH] if i + BATCH < len(codes) else codes[-1] + "~"
        r = _process_batch(cur, lo, hi, date_idx, meta)
        if r is not None:
            cnt, lu, pm, pm2, sec, lead = r
            cnt_parts.append(cnt)
            lu_parts.append(lu)
            pm_parts.append(pm)
            if not pm2.empty:
                pm2_parts.append(pm2)
            if not sec.empty:
                sec_parts.append(sec)
            if not lead.empty:
                lead_parts.append(lead)
        if (i // BATCH) % 5 == 0:
            log.info("batch %d/%d", i // BATCH + 1, (len(codes) + BATCH - 1) // BATCH)
    conn.close()

    cnt = pd.concat(cnt_parts).groupby("level_0" if False else "date").sum()
    base = pd.DataFrame(index=cnt.index)
    for c in ("total", "limit_up", "limit_down", "touch_limit", "up", "down", "flat",
              "turnover", "p1", "p1x", "p2", "p2x", "p3", "p3x", "pl", "plx",
              "lb2", "lb2s", "lb2b", "big_face", "heaven_hell"):
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

    # v3 P1: 昨涨停溢价(剔除今日一字开盘)
    if pm2_parts:
        pm2 = pd.concat(pm2_parts).groupby("date")["pct_chg"]
        base["premium_mean_noyizi"] = pm2.mean().round(3)
        base["premium_median_noyizi"] = pm2.median().round(3)

    # v3 P0: 涨跌幅分布 JSON(21档) + 全市场均涨/中位(直方图插值近似)
    bcols = [f"b{i}" for i in range(-10, 11)]
    base["chg_dist"] = cnt[bcols].apply(
        lambda r: json.dumps({str(i): int(r[f"b{i}"])
                              for i in range(-10, 11) if r[f"b{i}"] > 0}), axis=1)

    def _hist_median(row):
        n = row["pct_n"]
        if n <= 0:
            return np.nan
        half, cum = n / 2.0, 0.0
        for i in range(-10, 11):
            c = row[f"b{i}"]
            if c <= 0:
                continue
            if cum + c >= half:
                return i + (half - cum) / c     # 桶内线性插值
            cum += c
        return np.nan

    base["mkt_chg_mean"] = (cnt["pct_sum"] / cnt["pct_n"].replace(0, np.nan)).round(3)
    base["mkt_chg_median"] = [round(v, 3) if v == v else None
                              for v in (_hist_median(r) for _, r in cnt.iterrows())]

    # v3 P1: 连板值(昨连板股今>=7%接力比例) / 连比值(断板收平/跌比例)
    base["lb_strength"] = (cnt["lb2s"] / cnt["lb2"].replace(0, np.nan)).round(4)
    base["lb_break"] = (cnt["lb2b"] / cnt["lb2"].replace(0, np.nan)).round(4)

    # v3 P0: 板块日频聚合(跨批合并 + 全局龙头)
    sec = pd.concat(sec_parts).groupby(["date", "industry"], as_index=False).agg(
        turnover=("turnover", "sum"), stock_count=("stock_count", "sum"),
        up_count=("up_count", "sum"), pct_sum=("pct_sum", "sum"))
    lead = pd.concat(lead_parts).sort_values("pct").drop_duplicates(
        subset=["date", "industry"], keep="last")
    sec = sec.merge(lead, on=["date", "industry"], how="left")
    sec["chg_mean"] = (sec.pop("pct_sum") / sec["stock_count"].replace(0, np.nan)).round(3)
    sec = sec.rename(columns={"code": "lead_stock_code", "pct": "lead_chg"})
    sec["lead_stock"] = sec["lead_stock_code"].map(meta["name"])
    global _SECTOR_DF
    _SECTOR_DF = sec

    base["total_turnover"] = base.pop("turnover")
    base["up_ratio"] = base.pop("up") / base["total"]
    base["up_count"] = cnt["up"].astype(int)
    base["down_count"] = cnt["down"].astype(int)
    base["flat_count"] = cnt["flat"].astype(int)
    base["seal_rate"] = base["limit_up"] / base["touch_limit"].replace(0, np.nan)
    base["promo_1_2"] = base.pop("p1x") / base.pop("p1").replace(0, np.nan)
    base["promo_2_3"] = base.pop("p2x") / base.pop("p2").replace(0, np.nan)
    base["promo_3_up"] = base.pop("p3x") / base.pop("p3").replace(0, np.nan)
    base["promo_overall"] = base.pop("plx") / base.pop("pl").replace(0, np.nan)

    pct = pd.DataFrame({k: _epct(base[k]) for k in WEIGHTS})
    w_series = pd.Series(WEIGHTS)
    num = pct.mul(w_series, axis=1).sum(axis=1, skipna=True)
    den = pct.notna().mul(w_series, axis=1).sum(axis=1)
    base["composite"] = (num / den.replace(0, np.nan)).round(2)
    base["composite_ma5"] = base["composite"].rolling(5).mean().round(2)
    base["phase"] = base["composite"].map(_phase_label)
    base = base[base["limit_up"].notna()]
    return _merge_extras(base.reset_index(), extras)


# ---------------------------------------------------------------------------
# v2: 补充指标读取与合并(纯函数, 无网络, 可单测)
# ---------------------------------------------------------------------------

def _load_extras(cur):
    """读 sentiment_extras_daily -> DataFrame(date + 6列); 表缺失/为空返回空表(不阻断 v1)."""
    try:
        cur.execute("SELECT date, lhb_count, lhb_net_buy, lhb_inst_seats, lhb_inst_net_buy, lhb_inst_buy, lhb_total_buy, "
                    "margin_balance, margin_buy_amt, broken_count "
                    "FROM sentiment_extras_daily")
        rows = cur.fetchall()
    except pymysql.err.ProgrammingError:
        return pd.DataFrame()
    if not rows:
        return pd.DataFrame()
    ex = pd.DataFrame(rows, columns=["date"] + EXTRA_COLS)
    ex["date"] = pd.to_datetime(ex["date"]).dt.date
    for c in EXTRA_COLS:
        ex[c] = pd.to_numeric(ex[c], errors="coerce")
    return ex


def _merge_extras(base, extras):
    """v2: 合并补充指标, 计算 true_seal_rate / composite_v2 / phase_v2 (纯函数, 可单测).

    - extras 为空 => v2 各列 NaN, composite_v2 按 v1 六指标重加权(数值与 composite 一致)
    - 行级权重归一: 某子指标缺失(炸板池仅近30日/两融T+1)时按当日可用权重归一
    """
    b = base.copy()
    b["date"] = pd.to_datetime(b["date"]).dt.date
    if extras is None or extras.empty:
        for c in EXTRA_COLS:
            b[c] = np.nan
    else:
        b = b.merge(extras, on="date", how="left")
        for c in EXTRA_COLS:
            if c not in b.columns:
                b[c] = np.nan
    # 真实封板率(炸板池口径): 收盘涨停 / (收盘涨停 + 炸板), 修正日线 proxy 低估
    denom = b["limit_up"] + b["broken_count"]
    with np.errstate(invalid="ignore", divide="ignore"):
        b["true_seal_rate"] = np.where(
            b["broken_count"].notna() & (denom > 0), b["limit_up"] / denom, np.nan)

    # === 方案 A ===
    # 龙虎榜分项从"净买绝对值"改为"净买/总成交额*1e4 (bp)",
    # 消除成交扩容的时间趋势, 冷市不再因 lhb 历史膨胀而给出 80+ 高分
    with np.errstate(invalid="ignore", divide="ignore"):
        lhb_nb = pd.to_numeric(b.get("lhb_net_buy"), errors="coerce")
        tot = pd.to_numeric(b.get("total_turnover"), errors="coerce")
        # lhb_net_buy 单: 万; total_turnover 单: 原始stock_data_daily一致(元), 转万除以1e4 -> 比例 *1e4 = bp
        # 实际上 total_turnover 从 base 来是元量级, 需与 lhb_net_buy (万元) 对齐 -> 比例 = lhb*1e4/total
        b["lhb_ratio"] = np.where(
            tot.notna() & lhb_nb.notna() & (tot > 0),
            (lhb_nb * 1.0e4 / tot * 1.0e4).round(6),   # 净买占比 (bp) 再乘1e4 = 净买*1e8 / tot; 实际 bp 量级为正数/负数
            np.nan)
    # === 方案 A/B1: 按列选择分位算法(rolling vs expanding), 并让稀疏首段 NaN 不再拖垮全列 ===
    keys = [k for k in WEIGHTS_V2 if b[k].notna().any()]
    if keys:
        pct = pd.DataFrame({k: _epct(b[k], use_rolling=(k in ROLLING_PCT_KEYS)) for k in keys})
        ws = pd.Series({k: WEIGHTS_V2[k] for k in keys})
        num = pct.mul(ws, axis=1).sum(axis=1, skipna=True)
        den = pct.notna().mul(ws, axis=1).sum(axis=1)
        b["composite_v2"] = (num / den.replace(0, np.nan)).round(2)
    else:
        b["composite_v2"] = np.nan
    b["composite_v2_ma5"] = b["composite_v2"].rolling(5).mean().round(2)
    b["phase_v2"] = b["composite_v2"].map(_phase_label)
    # 猛男值/菜比值: 对标冰川口径的机构活跃度综合分位数(修正4项不合理)
    # 修正1: 用净买入(非毛买入)反映机构真实方向 — 做T时毛买大但净卖, 旧公式完全颠倒
    # 修正2: 用历史分位数(rolling 252天)替代固定tanh函数 — 自适应牛熊市, 无需手动调参
    # 修正3: 极端值强制边界 — 分位数在趋势市中钝化, 用绝对阈值修正 net_ratio < -0.10 → ≤25; >0.10 → ≥75
    # 修正4: 加入机构毛买占比分位(50:50综合) — 冰川的"猛男"是「资金强度+参与度」双指标:
    #   净买分位 = 反映资金方向(做多还是做空)
    #   毛买分位 = 反映参与强度(机构买了多少份额)
    #   综合 = 50% × 净买分位 + 50% × 毛买分位
    #   (实测: 8.13从36.9→31.8偏弱, 8.14从75.8→40.4偏弱, 与冰川一致)
    with np.errstate(invalid="ignore", divide="ignore"):
        inst_net = b.get("lhb_inst_net_buy")
        inst_buy = b.get("lhb_inst_buy")
        total_buy = b.get("lhb_total_buy")
        net_ratio = np.where(
            (total_buy > 0) & inst_net.notna(),
            inst_net / total_buy,
            np.nan)
        buy_ratio = np.where(
            (total_buy > 0) & inst_buy.notna(),
            inst_buy / total_buy,
            np.nan)
        # 50%净买方向分位 + 50%毛买参与度分位 = 综合猛男值
        pct_net = _epct(pd.Series(net_ratio, index=b.index), use_rolling=True)
        pct_buy = _epct(pd.Series(buy_ratio, index=b.index), use_rolling=True)
        b["masculinity_score"] = (0.5 * pct_net + 0.5 * pct_buy).round(2)
        # 极端值强制边界修正(仅用净买方向判断极端性, 避免毛买高但净卖的误判)
        _inst_sell_extreme = (pd.Series(net_ratio, index=b.index) < -0.10) & b["masculinity_score"].notna()
        _inst_buy_extreme  = (pd.Series(net_ratio, index=b.index) >  0.10) & b["masculinity_score"].notna()
        b.loc[_inst_sell_extreme, "masculinity_score"] = b.loc[_inst_sell_extreme, "masculinity_score"].clip(upper=25)
        b.loc[_inst_buy_extreme,  "masculinity_score"] = b.loc[_inst_buy_extreme, "masculinity_score"].clip(lower=75)
        b["retail_ratio"] = (100.0 - b["masculinity_score"]).round(2)
    # A2: 冰川6级温度计专用值(剔除龙虎榜项, 与冰川图只看涨停/连板/封板结构一致)
    glae_keys = [k for k in WEIGHTS_GLAE if b[k].notna().any()]
    if glae_keys:
        glae_pct = pd.DataFrame({
            k: _epct(b[k], use_rolling=(k in ROLLING_PCT_KEYS)) for k in glae_keys})
        gws = pd.Series({k: WEIGHTS_GLAE[k] for k in glae_keys})
        gnum = glae_pct.mul(gws, axis=1).sum(axis=1, skipna=True)
        gden = glae_pct.notna().mul(gws, axis=1).sum(axis=1)
        b["composite_glae"] = (gnum / gden.replace(0, np.nan)).round(2)
    else:
        b["composite_glae"] = np.nan
    # 缺失时回退 composite (v1 六指标也无龙虎榜, 天然对齐冰川口径)
    b["phase_glae"] = b["composite_glae"].fillna(b["composite"]).apply(_phase_glae_label)
    # 事件式强制触发: 分位法在极端区钝化(历史含更惨日), 用绝对条件确认两端
    # (社区实证"冰点五信号"思路: 跌停>涨停x3 / 红盘占比<15%; 连板高度>=7 / 封板率>85%)
    _gbase = b["composite_glae"].fillna(b["composite"])
    _ice = (_gbase < 25) & (
        (b["limit_down"] > b["limit_up"] * 3) | (b["up_ratio"] < 0.15))
    _boil = (_gbase > 85) & (
        (b["max_streak"] >= 7) | (b["seal_rate"] > 0.85))
    b.loc[_ice, "phase_glae"] = "冰点"
    b.loc[_boil, "phase_glae"] = "沸点"
    return b


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
  lhb_count INT, lhb_net_buy DECIMAL(14,2), lhb_inst_seats INT, lhb_inst_net_buy DECIMAL(14,2), lhb_inst_buy DECIMAL(14,2), lhb_total_buy DECIMAL(14,2),
  margin_balance DECIMAL(12,2), margin_buy_amt DECIMAL(12,2),
  broken_count INT, true_seal_rate DECIMAL(6,4),
  composite_v2 DECIMAL(6,2), composite_v2_ma5 DECIMAL(6,2), phase_v2 VARCHAR(8),
  chg_dist VARCHAR(600),
  up_count INT, down_count INT, flat_count INT,
  mkt_chg_mean DECIMAL(6,3), mkt_chg_median DECIMAL(6,3),
  premium_mean_noyizi DECIMAL(7,3), premium_median_noyizi DECIMAL(7,3),
  lb_strength DECIMAL(6,4), lb_break DECIMAL(6,4),
  masculinity_score DECIMAL(6,2), retail_ratio DECIMAL(6,2),
  phase_glae VARCHAR(8),
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

COLS = ["date", "limit_up", "limit_down", "touch_limit", "seal_rate", "max_streak",
        "streak_dist", "promo_1_2", "promo_2_3", "promo_3_up", "promo_overall",
        "premium_mean", "premium_median", "big_face", "heaven_hell", "up_ratio",
        "total_turnover", "composite", "composite_ma5", "phase",
        "lhb_count", "lhb_net_buy", "lhb_inst_seats", "lhb_inst_net_buy", "lhb_inst_buy", "lhb_total_buy", "margin_balance",
        "margin_buy_amt", "broken_count", "true_seal_rate",
        "composite_v2", "composite_v2_ma5", "phase_v2",
        "chg_dist", "up_count", "down_count", "flat_count",
        "mkt_chg_mean", "mkt_chg_median",
        "premium_mean_noyizi", "premium_median_noyizi",
        "lb_strength", "lb_break",
        "masculinity_score", "retail_ratio", "composite_glae", "phase_glae"]

# 老表补列(MySQL 无 ADD COLUMN IF NOT EXISTS, 1060=已存在则跳过)
V2_COLS_DDL = [
    ("lhb_count", "INT"),
    ("lhb_net_buy", "DECIMAL(14,2)"),
    ("lhb_inst_seats", "INT"),
    ("lhb_inst_net_buy", "DECIMAL(14,2)"),
    ("lhb_inst_buy", "DECIMAL(14,2)"),
    ("lhb_total_buy", "DECIMAL(14,2)"),
    ("margin_balance", "DECIMAL(12,2)"),
    ("margin_buy_amt", "DECIMAL(12,2)"),
    ("broken_count", "INT"),
    ("true_seal_rate", "DECIMAL(6,4)"),
    ("composite_v2", "DECIMAL(6,2)"),
    ("composite_v2_ma5", "DECIMAL(6,2)"),
    ("phase_v2", "VARCHAR(8)"),
    ("chg_dist", "VARCHAR(600)"),
    ("up_count", "INT"),
    ("down_count", "INT"),
    ("flat_count", "INT"),
    ("mkt_chg_mean", "DECIMAL(6,3)"),
    ("mkt_chg_median", "DECIMAL(6,3)"),
    ("premium_mean_noyizi", "DECIMAL(7,3)"),
    ("premium_median_noyizi", "DECIMAL(7,3)"),
    ("lb_strength", "DECIMAL(6,4)"),
    ("lb_break", "DECIMAL(6,4)"),
    ("masculinity_score", "DECIMAL(6,2)"),
    ("retail_ratio", "DECIMAL(6,2)"),
    ("composite_glae", "DECIMAL(6,2)"),
    ("phase_glae", "VARCHAR(8)"),
]


def _migrate(cur):
    for col, ddl in V2_COLS_DDL:
        try:
            cur.execute(f"ALTER TABLE sentiment_daily ADD COLUMN {col} {ddl}")
        except pymysql.err.OperationalError as e:
            if e.args[0] != 1060:
                raise


def persist(base, tail_days):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(DDL)
    _migrate(cur)
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


SECTOR_DDL = """
CREATE TABLE IF NOT EXISTS sentiment_sector_daily (
  date DATE NOT NULL,
  industry VARCHAR(50) NOT NULL,
  stock_count INT, up_count INT,
  turnover DECIMAL(18,2), chg_mean DECIMAL(6,3),
  lead_stock VARCHAR(32), lead_stock_code VARCHAR(12), lead_chg DECIMAL(6,2),
  PRIMARY KEY (date, industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

SECTOR_COLS = ["date", "industry", "stock_count", "up_count", "turnover",
               "chg_mean", "lead_stock", "lead_stock_code", "lead_chg"]


def persist_sectors(sec, tail_days):
    """板块日频表: 保留最近 tail_days 个交易日, 先删后插(整日重算幂等)."""
    if sec is None or sec.empty:
        log.info("sectors: 无数据, 跳过")
        return
    dates_sorted = sorted(sec["date"].unique())
    keep = set(dates_sorted[-tail_days:])
    sub = sec[sec["date"].isin(keep)]
    if sub.empty:
        return
    conn = _conn()
    cur = conn.cursor()
    cur.execute(SECTOR_DDL)
    cur.execute("DELETE FROM sentiment_sector_daily WHERE date >= %s", (min(keep),))
    rows = []
    for r in sub.to_dict("records"):
        vals = []
        for c in SECTOR_COLS:
            v = r.get(c)
            if isinstance(v, float) and np.isnan(v):
                v = None
            vals.append(v)
        rows.append(vals)
    cur.executemany(
        "INSERT INTO sentiment_sector_daily ({}) VALUES ({})".format(
            ",".join(SECTOR_COLS), ",".join(["%s"] * len(SECTOR_COLS))),
        rows)
    conn.commit()
    conn.close()
    log.info("persisted sectors: %d rows, %d days, %d industries",
             len(rows), len(keep), sub["industry"].nunique())


# ---------------------------------------------------------------------------
# v2 补充指标采集(AKShare EOD, 仅 --collect-extras 触达; 各组失败容忍, 不阻断 v1)
# ---------------------------------------------------------------------------

EXTRAS_DDL = """
CREATE TABLE IF NOT EXISTS sentiment_extras_daily (
  date DATE NOT NULL PRIMARY KEY,
  lhb_count INT, lhb_net_buy DECIMAL(14,2), lhb_inst_seats INT, lhb_inst_net_buy DECIMAL(14,2), lhb_inst_buy DECIMAL(14,2), lhb_total_buy DECIMAL(14,2),
  margin_balance DECIMAL(12,2), margin_buy_amt DECIMAL(12,2),
  broken_count INT,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def _norm_date(v):
    """akshare 日期(str YYYY-MM-DD / str YYYYMMDD / Timestamp) -> 'YYYY-MM-DD'"""
    s = str(v)[:10]
    if len(s) == 8 and s.isdigit():
        s = f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s


def _retry(fn, what):
    for i in range(EXTRAS_RETRY):
        try:
            return fn()
        except Exception as e:
            if i == EXTRAS_RETRY - 1:
                log.warning("%s 失败(重试%d次): %s", what, EXTRAS_RETRY, e)
                return None
            time.sleep(2 * (i + 1))


def _fetch_lhb(start, end):
    """区间龙虎榜明细 -> {date: {lhb_count, lhb_net_buy, lhb_inst_seats}}; 净买额 元->万."""
    df = _retry(lambda: ak.stock_lhb_detail_em(
        start_date=start.replace("-", ""), end_date=end.replace("-", "")),
        f"龙虎榜[{start}~{end}]")
    if df is None or df.empty:
        return {}
    # 注意: 同一股票同日可能有多条记录(不同席位类型), 不应去重, 应全部汇总
    per = {}
    for d, sub in df.groupby("上榜日"):
        nb = pd.to_numeric(sub["龙虎榜净买额"], errors="coerce").fillna(0.0).sum()
        # 机构席位口径: 仅"机构"和"主力"席位(剔除"买一"和地区游资)
        # 买一是当天最大买家(不一定是机构), 地区关键词代表游资/小资金
        # 对标冰川猛男值: 只计真正的机构/主力资金, 不含游资席位
        jd = sub["解读"].astype(str) if "解读" in sub.columns else pd.Series([""]*len(sub))
        is_inst = jd.str.contains("机构|主力")
        inst = int(is_inst.sum())
        inst_nb = pd.to_numeric(sub.loc[is_inst, "龙虎榜净买额"], errors="coerce").fillna(0.0).sum() if inst > 0 else 0.0
        inst_buy = pd.to_numeric(sub.loc[is_inst, "龙虎榜买入额"], errors="coerce").fillna(0.0).sum() if inst > 0 else 0.0
        total_buy = pd.to_numeric(sub["龙虎榜买入额"], errors="coerce").fillna(0.0).sum()
        per[_norm_date(d)] = {"lhb_count": int(len(sub)),
                              "lhb_net_buy": round(float(nb) / 1e4, 2),
                              "lhb_inst_seats": inst,
                              "lhb_inst_net_buy": round(float(inst_nb) / 1e4, 2),
                              "lhb_inst_buy": round(float(inst_buy) / 1e4, 2),
                              "lhb_total_buy": round(float(total_buy) / 1e4, 2)}
    return per


def _keepalive(cur):
    """DB 连接保活(服务器 wait_timeout=600, 采集期间长时间无写入会被掐断)."""
    try:
        cur.connection.ping(reconnect=True)
    except Exception as e:
        log.warning("keepalive ping 失败(忽略): %s", e)


def _collect_lhb(cur, target, force, existing):
    todo = [d for d in target if force or d not in existing["lhb_count"]]
    if not todo:
        log.info("extras.lhb 无缺口")
        return
    got = 0
    import calendar
    for m in sorted({d[:7] for d in todo}):          # 按月分块, 避免单次拉取页数过多
        _keepalive(cur)
        y, mo = map(int, m.split("-"))
        per = _fetch_lhb(f"{m}-01", f"{m}-{calendar.monthrange(y, mo)[1]:02d}")
        got += _upsert_many(cur, per)
    log.info("extras.lhb 待补 %d 日, 覆盖 %d 日", len(todo), got)


def _collect_margin(cur, target, force, existing):
    """两融采集(方案 B2 重构):
    主路: ak.macro_china_market_margin_sh / macro_china_market_margin_sz
         — 东方财富汇总接口, 覆盖多年历史, 绕过上交所/深交所直连限流/封禁, 一次 HTTP 即完整返回;
    辅路: 原 stock_margin_sse + stock_margin_szse 仅在 macro 接口不可用时兜底;
    输出单位: margin_balance / margin_buy_amt 统一 亿元.
    """
    todo = [d for d in target if force or d not in existing["margin_balance"]]
    if not todo:
        log.info("extras.margin 无缺口")
        return
    got = 0

    # --- 主路: macro 汇总接口(沪/深各自一张完整全历史表, 1~2 次请求搞定, 47 机已验证可访问) ---
    def _parse_macro(df, d_col, bal_col, buy_col):
        out = {}
        if df is None or df.empty:
            return out
        for _, r in df.iterrows():
            try:
                d = _norm_date(r[d_col])
                bal = float(r[bal_col]) / 1e8
                buy = float(r[buy_col]) / 1e8
                if bal >= 0 and buy >= 0:
                    out[d] = (bal, buy)
            except (TypeError, ValueError, KeyError):
                continue
        return out

    sse = {}
    sz = {}
    # 先用 macro 接口(批量, 不耗流)
    sh_macro = _retry(lambda: ak.macro_china_market_margin_sh(), "两融-沪[macro]")
    sse = _parse_macro(sh_macro, "日期", "融资余额", "融资买入额")
    sz_macro = _retry(lambda: ak.macro_china_market_margin_sz(), "两融-深[macro]")
    sz = _parse_macro(sz_macro, "日期", "融资余额", "融资买入额")
    log.info("extras.margin 主路 macro: 沪 %d 日, 深 %d 日 (完整历史)", len(sse), len(sz))

    # --- 辅路(兜底): 若 macro 接口缺失, 尝试原始 SSE/SZSE 接口补齐 todo ---
    if len(sse) < 10 or len(sz) < 10:
        lo, hi = todo[0].replace("-", ""), todo[-1].replace("-", "")
        sse_df = _retry(lambda: ak.stock_margin_sse(start_date=lo, end_date=hi),
                        f"两融-沪[兜底 {lo}~{hi}]")
        if sse_df is not None and not sse_df.empty:
            for _, r in sse_df.iterrows():
                try:
                    d = _norm_date(r["信用交易日期"])
                    if d not in sse:
                        sse[d] = (float(r["融资余额"]) / 1e8, float(r["融资买入额"]) / 1e8)
                except (TypeError, ValueError, KeyError):
                    pass
        consec_fail = 0
        for d in todo:
            if d in sse and d in sz:
                continue
            _keepalive(cur)
            if d not in sse:
                continue
            sz_row = _retry(lambda: ak.stock_margin_szse(date=d.replace("-", "")), f"两融-深[兜底 {d}]")
            if sz_row is None or sz_row.empty:
                consec_fail += 1
                if consec_fail >= 10:
                    log.warning("extras.margin 辅路 连续失败(疑似限流), 中止本组", consec_fail)
                    break
                continue
            try:
                r = sz_row.iloc[0]
                if d not in sz:
                    sz[d] = (float(r["融资余额"]), float(r["融资买入额"]))  # SZSE 原生亿元
            except (KeyError, TypeError, ValueError):
                pass
            time.sleep(EXTRAS_SLEEP)

    # --- 写入 ---
    written = set()
    for d in todo:
        if d not in sse or d not in sz:
            continue                           # 任一市场暂缺(T+1公布/节假日), 留待下次补
        _upsert(cur, d, {
            "margin_balance": round(sse[d][0] + sz[d][0], 2),
            "margin_buy_amt": round(sse[d][1] + sz[d][1], 2)})
        written.add(d)
        got += 1
    log.info("extras.margin 待补 %d 日, 合成写入 %d 日 (macro 沪 %d/深 %d)",
             len(todo), got, len(sse), len(sz))


def _collect_broken(cur, target, force, existing, lookback=30):
    # 炸板池仅近 ~30 交易日可得, 无历史回填
    todo = [d for d in target[-lookback:] if force or d not in existing["broken_count"]]
    if not todo:
        log.info("extras.broken 无缺口")
        return
    got = 0
    consec_fail = 0
    for d in todo:
        _keepalive(cur)
        df = _retry(lambda: ak.stock_zt_pool_zbgc_em(date=d.replace("-", "")),
                    f"炸板池[{d}]")
        if df is None:
            consec_fail += 1
            if consec_fail >= 10:
                log.warning("extras.broken 连续 %d 日失败, 中止本组待下次补", consec_fail)
                break
            continue
        consec_fail = 0
        # 近30日窗口内空表 => 当日真实无炸板, 记 0 防死循环重试
        _upsert(cur, d, {"broken_count": int(len(df))})
        got += 1
        time.sleep(EXTRAS_SLEEP)
    log.info("extras.broken 待补 %d 日, 写入 %d 日", len(todo), got)


def _upsert(cur, date_str, fields):
    """只更新本组字段(INSERT ... ON DUPLICATE KEY UPDATE), 各组互不覆盖."""
    cols = list(fields.keys())
    cur.execute(
        "INSERT INTO sentiment_extras_daily (date, {c}) VALUES ({p}) "
        "ON DUPLICATE KEY UPDATE {u}".format(
            c=",".join(cols), p=",".join(["%s"] * (len(cols) + 1)),
            u=",".join(f"{k}=VALUES({k})" for k in cols)),
        [date_str] + [fields[k] for k in cols])
    return 1


def _upsert_many(cur, per):
    return sum(_upsert(cur, d, f) for d, f in per.items())


def _existing(cur):
    """各组已写入(非 NULL)日期集合 -> {col: set('YYYY-MM-DD')}"""
    ex = {c: set() for c in EXTRA_COLS}
    for c in EXTRA_COLS:
        try:
            cur.execute(f"SELECT date FROM sentiment_extras_daily WHERE {c} IS NOT NULL")
            ex[c] = {str(r[0]) for r in cur.fetchall()}
        except pymysql.err.ProgrammingError:
            pass
    return ex


def collect_extras(backfill=False, only=None, force=False):
    """AKShare EOD 补充指标采集入口. 北向净买额已停发(2024-08-18)不采集."""
    if ak is None:
        log.error("akshare 未安装, 无法采集补充指标: pip install akshare")
        raise SystemExit(1)
    conn = _conn()
    cur = conn.cursor()
    cur.execute(EXTRAS_DDL)
    cur.execute("SELECT DISTINCT date FROM stock_data_daily ORDER BY date")
    all_dates = [str(r[0]) for r in cur.fetchall()]
    target = ([d for d in all_dates if d >= EXTRAS_FROM] if backfill
              else all_dates[-30:])
    if not target:
        log.error("stock_data_daily 无交易日历")
        raise SystemExit(1)
    log.info("extras 目标 %d 交易日 (%s ~ %s)", len(target), target[0], target[-1])
    existing = _existing(cur)
    try:
        if only in (None, "lhb"):
            _collect_lhb(cur, target, force, existing)
        if only in (None, "margin"):
            _collect_margin(cur, target, force, existing)
        if only in (None, "broken"):
            _collect_broken(cur, target, force, existing)
        conn.commit()
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true", help="回填全部交易日")
    ap.add_argument("--days", type=int, default=30, help="重算近 N 交易日(默认30)")
    ap.add_argument("--collect-extras", action="store_true",
                    help="联网采集补充指标(龙虎榜/两融/炸板池)后再计算")
    ap.add_argument("--extras-backfill", action="store_true",
                    help="补充指标全量回填(配合 --collect-extras, 计算亦全量)")
    ap.add_argument("--only", choices=["lhb", "margin", "broken"],
                    help="只采集指定组(修复用, 不触发计算)")
    ap.add_argument("--force", action="store_true", help="忽略已有值强制重抓")
    args = ap.parse_args()

    if args.collect_extras or args.only:
        collect_extras(backfill=args.extras_backfill, only=args.only, force=args.force)
        if args.only:
            return

    base = compute()
    tail = len(base) if (args.backfill or args.extras_backfill) else args.days
    persist(base, tail)
    persist_sectors(_SECTOR_DF, tail)
    last = base.iloc[-1]
    log.info("latest %s composite=%s phase=%s | v2=%s phase2=%s lu=%d ld=%d max_streak=%s",
             last["date"], last["composite"], last["phase"],
             last["composite_v2"], last["phase_v2"],
             int(last["limit_up"]), int(last["limit_down"]), last["max_streak"])


if __name__ == "__main__":
    main()
