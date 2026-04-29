"""推送服务 - 邮件发送（早报+周报+异动提醒）"""
import json, logging, os, smtplib, sqlite3
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"

# SMTP 配置通过环境变量注入，后续在 systemd service 中配置
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_SSL = os.environ.get("SMTP_SSL", "true").lower() == "true"


def _get_push_configs():
    """获取所有启用推送的用户配置"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM push_configs WHERE email IS NOT NULL AND email != ''").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _send_email(to_email, subject, html_body):
    """发送单封邮件"""
    if not SMTP_HOST or not SMTP_USER:
        logger.warning("SMTP 未配置，跳过发送: %s → %s", subject, to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if SMTP_SSL:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        logger.info("邮件已发送: %s → %s", subject, to_email)
        return True
    except Exception as e:
        logger.error("邮件发送失败: %s → %s: %s", subject, to_email, e)
        return False


def send_daily_brief():
    """发送每日早报"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 获取热度数据
    heat = conn.execute("""
        SELECT t.name, h.score, h.news_count,
               (h.score - COALESCE(prev.score, h.score)) as change
        FROM tracks t
        LEFT JOIN track_heat_daily h ON h.track_id=t.id
            AND h.date=(SELECT MAX(date) FROM track_heat_daily WHERE track_id=t.id)
        LEFT JOIN track_heat_daily prev ON prev.track_id=t.id
            AND prev.date=(SELECT MAX(date) FROM track_heat_daily WHERE track_id=t.id AND date < h.date)
        WHERE t.status='active'
    """).fetchall()

    # 获取今日要闻
    news = conn.execute(
        "SELECT title, source, publish_time FROM financial_news ORDER BY publish_time DESC LIMIT 5"
    ).fetchall()
    conn.close()

    today = datetime.now().strftime("%Y-%m-%d")
    heat_rows = "".join(
        f"<tr><td>{r['name']}</td><td><b>{r['score'] or '-'}</b></td>"
        f"<td style='color:{'#52c41a' if (r['change'] or 0)>=0 else '#ff4d4f'}'>"
        f"{'↑' if (r['change'] or 0)>=0 else '↓'}{abs(r['change'] or 0):.1f}</td></tr>"
        for r in heat
    )
    news_items = "".join(f"<li>{r['title']}</li>" for r in news)

    html = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto">
<h2 style="color:#1890ff">📊 D8Q 每日早报 - {today}</h2>
<h3>赛道热度</h3>
<table style="width:100%;border-collapse:collapse;font-size:14px">
<tr style="background:#f5f5f5"><th style="padding:8px;text-align:left">赛道</th><th>热度</th><th>变化</th></tr>
{heat_rows}</table>
<h3 style="margin-top:16px">今日要闻</h3>
<ol style="font-size:14px;line-height:1.8">{news_items}</ol>
<p style="color:#999;font-size:12px;margin-top:20px">—— D8Q 智能资讯平台</p></div>"""

    configs = _get_push_configs()
    sent = 0
    for cfg in configs:
        types = json.loads(cfg.get("enabled_types") or "[]")
        if "daily_brief" in types:
            if _send_email(cfg["email"], f"[D8Q] {today} 赛道早报", html):
                sent += 1
    logger.info("每日早报发送完成: %d/%d", sent, len(configs))
    return sent


def send_heat_alert(track_name, score, change):
    """发送热度异动提醒"""
    html = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto">
<h2 style="color:#fa8c16">🔥 热度异动提醒</h2>
<p style="font-size:16px">赛道「<b>{track_name}</b>」热度指数 <b>{score}</b>，较昨日上升 <b style="color:#ff4d4f">{change:.1f}%</b></p>
<p style="color:#999;font-size:12px;margin-top:20px">—— D8Q 智能资讯平台</p></div>"""

    configs = _get_push_configs()
    sent = 0
    for cfg in configs:
        types = json.loads(cfg.get("enabled_types") or "[]")
        threshold = cfg.get("alert_threshold", 30)
        if "heat_alert" in types and change >= threshold:
            if _send_email(cfg["email"], f"[D8Q] 🔥 {track_name} 热度异动 +{change:.0f}%", html):
                sent += 1
    return sent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("SMTP配置:", "已配置" if SMTP_HOST else "未配置（需设置环境变量）")
    print("推送用户:", len(_get_push_configs()))
    if SMTP_HOST:
        send_daily_brief()
    else:
        print("跳过发送（SMTP_HOST 未设置）")
        print("配置方式: 在 /etc/systemd/system/d8q-factory.service 中添加:")
        print("  Environment=SMTP_HOST=smtp.qq.com")
        print("  Environment=SMTP_PORT=465")
        print("  Environment=SMTP_USER=your@qq.com")
        print("  Environment=SMTP_PASS=your_auth_code")
