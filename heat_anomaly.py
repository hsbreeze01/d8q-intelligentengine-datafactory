"""热度异动检测 + 政策影响分析 - 每日定时任务"""
import json
import logging
import sqlite3
import urllib.request

logger = logging.getLogger(__name__)

DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"


def detect_heat_anomaly():
    """检测热度异动：今日 vs 昨日涨幅超阈值的赛道，触发邮件告警"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT t.name, h.score,
                   COALESCE(prev.score, 0) as prev_score
            FROM tracks t
            JOIN track_heat_daily h ON h.track_id=t.id
                AND h.date=(SELECT MAX(date) FROM track_heat_daily WHERE track_id=t.id)
            LEFT JOIN track_heat_daily prev ON prev.track_id=t.id
                AND prev.date=(SELECT MAX(date) FROM track_heat_daily WHERE track_id=t.id AND date < h.date)
            WHERE t.status='active' AND h.score > 0
        """).fetchall()
    finally:
        conn.close()

    alerts = []
    for r in rows:
        score = r["score"]
        prev = r["prev_score"] or 1
        change_pct = ((score - prev) / prev) * 100 if prev > 0 else 0
        if change_pct >= 30:  # default threshold
            alerts.append({"track": r["name"], "score": score, "change": change_pct})

    # 发送告警
    from push_service import send_heat_alert
    sent = 0
    for a in alerts:
        sent += send_heat_alert(a["track"], a["score"], a["change"])
        logger.info("热度异动告警: %s score=%.1f change=+%.1f%%", a["track"], a["score"], a["change"])

    return {"alerts": len(alerts), "sent": sent}


def run_policy_analysis():
    """调用 data-agent 的政策分析接口"""
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/tracks/policy-analysis",
            method="POST", data=b"",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        logger.info("政策分析完成: %s", result)
        return result
    except Exception as e:
        logger.warning("政策分析调用失败: %s", e)
        return {"error": str(e)}


def run_investment_collection():
    """调用 data-agent 的投融资采集接口"""
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/tracks/collect-investments",
            method="POST", data=b"",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
        logger.info("投融资采集完成: %s", result)
        return result
    except Exception as e:
        logger.warning("投融资采集调用失败: %s", e)
        return {"error": str(e)}
