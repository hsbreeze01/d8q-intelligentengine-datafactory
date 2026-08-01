"""智能预警扫描器 - 定时扫描预警规则并生成预警"""
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

AGENT_API = "http://localhost:8000"


def agent_request(method, path, data=None):
    """Proxy request to agent API"""
    url = AGENT_API + urllib.parse.quote(path, safe='/:?=&')
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return json.loads(_raw), e.code
        except (json.JSONDecodeError, ValueError):
            return {"error": f"HTTP {e.code}"}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


def _get_db_ctx():
    """延迟导入 get_db_ctx"""
    from datafactory.infrastructure.db_utils import get_db_ctx
    return get_db_ctx


def _check_cooldown(rule):
    """检查冷却时间，返回 True 表示仍在冷却中（不应触发）"""
    last_triggered = rule.get("last_triggered_at")
    if not last_triggered:
        return False
    try:
        last_dt = datetime.strptime(last_triggered, "%Y-%m-%d %H:%M:%S")
        cooldown = timedelta(hours=rule.get("cooldown_hours", 4))
        return datetime.now() < last_dt + cooldown
    except (ValueError, TypeError):
        return False


def _create_alert(user_id, rule_id, alert_type, severity, title, message, context=None):
    """写入 alerts 表并更新规则的 last_triggered_at"""
    get_db_ctx = _get_db_ctx()
    try:
        context_json = json.dumps(context, ensure_ascii=False) if context else None
        with get_db_ctx() as conn:
            conn.execute(
                "INSERT INTO alerts (user_id, rule_id, alert_type, severity, title, message, context_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (user_id, rule_id, alert_type, severity, title, message, context_json)
            )
            conn.execute(
                "UPDATE alert_rules SET last_triggered_at=datetime('now') WHERE id=?",
                (rule_id,)
            )
            conn.commit()
        logger.info("预警已创建: [%s] %s - %s", severity, title, user_id)
        # 如果是紧急预警，发送邮件
        if severity == "urgent":
            _send_urgent_email({
                "user_id": user_id,
                "title": title,
                "message": message,
                "severity": severity,
            })
    except Exception as e:
        logger.error("创建预警失败: %s", e)


def _send_urgent_email(alert):
    """对 urgent 级别调用 push_service 发送邮件"""
    try:
        from push_service import _get_push_configs, _send_email
        configs = _get_push_configs()
        user_config = next((c for c in configs if c.get("user_id") == alert["user_id"]), None)
        if not user_config or not user_config.get("email"):
            logger.info("用户 %s 未配置邮箱，跳过紧急邮件", alert["user_id"])
            return
        subject = f"[紧急预警] {alert['title']}"
        html_body = (
            f"<h2>⚠️ 紧急预警</h2>"
            f"<p><strong>{alert['title']}</strong></p>"
            f"<p>{alert.get('message', '')}</p>"
            f"<p style='color:#999;font-size:12px;'>此邮件由D8Q智能预警系统自动发送</p>"
        )
        _send_email(user_config["email"], subject, html_body)
        logger.info("紧急预警邮件已发送: %s -> %s", alert["title"], user_config["email"])
    except Exception as e:
        logger.error("发送紧急预警邮件失败: %s", e)


def scan_track_alerts(rules):
    """扫描赛道热度预警"""
    for rule in rules:
        try:
            if _check_cooldown(rule):
                continue
            condition = json.loads(rule["condition_json"])
            threshold = condition.get("threshold", 80)
            # 获取赛道热度数据
            data, code = agent_request("GET", "/api/tracks/heat")
            if code != 200 or not isinstance(data, dict):
                continue
            tracks = data.get("data") or data.get("tracks") or []
            if isinstance(tracks, list):
                for track in tracks:
                    heat = track.get("heat_score") or track.get("heat") or 0
                    track_name = track.get("name") or track.get("track_name", "未知")
                    if heat > threshold:
                        _create_alert(
                            user_id=rule["user_id"],
                            rule_id=rule["id"],
                            alert_type="track_heat",
                            severity=rule.get("severity", "normal"),
                            title=f"赛道热度预警: {track_name} 热度达 {heat}",
                            message=f"赛道「{track_name}」当前热度 {heat}，超过阈值 {threshold}",
                            context={"track_name": track_name, "heat_score": heat, "threshold": threshold}
                        )
                        break  # 每条规则每次只生成一条预警
        except Exception as e:
            logger.error("赛道热度扫描异常(rule=%s): %s", rule.get("id"), e)


def scan_funding_alerts(rules):
    """扫描投融资预警"""
    for rule in rules:
        try:
            if _check_cooldown(rule):
                continue
            condition = json.loads(rule["condition_json"])
            threshold = condition.get("threshold", 10000)  # 万元
            # 获取最近30分钟的投融资事件
            data, code = agent_request("GET", "/api/investment/events?minutes=30")
            if code != 200:
                # 尝试备选路径
                data, code = agent_request("GET", "/api/news?category=investment&limit=10")
            if code != 200 or not isinstance(data, dict):
                continue
            events = data.get("data") or data.get("events") or data.get("items") or []
            if isinstance(events, list):
                for event in events:
                    amount = event.get("amount") or event.get("funding_amount") or 0
                    if isinstance(amount, str):
                        try:
                            amount = float(amount.replace("万", "").replace("亿", "0000").replace(",", ""))
                        except ValueError:
                            continue
                    if amount > threshold:
                        company = event.get("company") or event.get("title", "未知企业")
                        _create_alert(
                            user_id=rule["user_id"],
                            rule_id=rule["id"],
                            alert_type="funding",
                            severity=rule.get("severity", "normal"),
                            title=f"融资预警: {company} 融资 {amount}万元",
                            message=f"「{company}」获得融资 {amount}万元，超过阈值 {threshold}万元",
                            context={"company": company, "amount": amount, "threshold": threshold}
                        )
                        break
        except Exception as e:
            logger.error("融资扫描异常(rule=%s): %s", rule.get("id"), e)


def scan_policy_alerts(rules):
    """扫描政策类预警"""
    for rule in rules:
        try:
            if _check_cooldown(rule):
                continue
            condition = json.loads(rule["condition_json"])
            keywords = condition.get("keywords", ["重大", "突发", "紧急"])
            # 获取政策类资讯
            data, code = agent_request("GET", "/api/news?category=policy&limit=10")
            if code != 200 or not isinstance(data, dict):
                continue
            items = data.get("data") or data.get("items") or data.get("news") or []
            if isinstance(items, list):
                for item in items:
                    title = item.get("title", "")
                    content = item.get("summary") or item.get("content", "")
                    text = title + content
                    if any(kw in text for kw in keywords):
                        _create_alert(
                            user_id=rule["user_id"],
                            rule_id=rule["id"],
                            alert_type="policy",
                            severity=rule.get("severity", "urgent"),
                            title=f"政策预警: {title[:50]}",
                            message=f"检测到政策动态: {title}",
                            context={"title": title, "keywords_matched": [kw for kw in keywords if kw in text]}
                        )
                        break
        except Exception as e:
            logger.error("政策扫描异常(rule=%s): %s", rule.get("id"), e)


def scan_stock_alerts(rules):
    """扫描个股评分变化预警"""
    get_db_ctx = _get_db_ctx()
    for rule in rules:
        try:
            if _check_cooldown(rule):
                continue
            condition = json.loads(rule["condition_json"])
            threshold = condition.get("threshold", 10)
            # 检查 score_history 表是否存在
            with get_db_ctx() as conn:
                table_exists = conn.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='score_history'"
                ).fetchone()[0]
                if not table_exists:
                    continue
                # 获取最近有较大变化的股票
                rows = conn.execute(
                    "SELECT stock_code, stock_name, score, prev_score "
                    "FROM score_history "
                    "WHERE abs(score - prev_score) > ? "
                    "AND created_at > datetime('now', '-30 minutes') "
                    "LIMIT 5",
                    (threshold,)
                ).fetchall()
                for row in rows:
                    stock_code = row[0]
                    stock_name = row[1] or stock_code
                    score = row[2]
                    prev_score = row[3]
                    change = score - prev_score
                    _create_alert(
                        user_id=rule["user_id"],
                        rule_id=rule["id"],
                        alert_type="stock_score",
                        severity=rule.get("severity", "normal"),
                        title=f"评分变化: {stock_name} {'+' if change > 0 else ''}{change:.1f}分",
                        message=f"「{stock_name}」({stock_code}) 评分从 {prev_score:.1f} 变为 {score:.1f}，变化 {change:.1f} 分",
                        context={"stock_code": stock_code, "stock_name": stock_name, "score": score, "prev_score": prev_score, "change": change}
                    )
                    break  # 每条规则只触发一次
        except Exception as e:
            logger.error("个股评分扫描异常(rule=%s): %s", rule.get("id"), e)


def scan_all_alerts():
    """主扫描函数: 读取所有启用的规则，按类型分发扫描"""
    logger.info("开始预警扫描...")
    get_db_ctx = _get_db_ctx()
    try:
        with get_db_ctx() as conn:
            conn.row_factory = __import__("sqlite3").Row
            rows = conn.execute(
                "SELECT * FROM alert_rules WHERE enabled=1"
            ).fetchall()
        rules = [dict(r) for r in rows]
    except Exception as e:
        logger.error("读取预警规则失败: %s", e)
        return

    if not rules:
        logger.info("无启用的预警规则，跳过扫描")
        return

    # 按类型分组
    rules_by_type = {}
    for rule in rules:
        rt = rule.get("rule_type", "")
        rules_by_type.setdefault(rt, []).append(rule)

    # 分发扫描
    scanners = {
        "track_heat": scan_track_alerts,
        "funding": scan_funding_alerts,
        "policy": scan_policy_alerts,
        "stock_score": scan_stock_alerts,
    }

    for rule_type, type_rules in rules_by_type.items():
        scanner = scanners.get(rule_type)
        if scanner:
            try:
                scanner(type_rules)
            except Exception as e:
                logger.error("扫描器 %s 异常: %s", rule_type, e)
        else:
            logger.warning("未知规则类型: %s", rule_type)

    logger.info("预警扫描完成，共处理 %d 条规则", len(rules))
