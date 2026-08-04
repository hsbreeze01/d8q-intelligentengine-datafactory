"""D8Q 智能资讯工厂 - 前后端一体 Web 应用 v2 (含任务管理)"""
import json
import re
import logging
import os
import secrets
import sys
import urllib.request
import urllib.parse
from contextlib import contextmanager
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, session
import time as _time

from auth import auth_bp, check_auth
from export_weekly import export_bp
from prompts_api import bp as prompts_bp
from compass_pages import compass_bp
from investment_api import investment_bp

logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- 认证与权限 ---
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
app.register_blueprint(auth_bp)
app.before_request(check_auth)

# [DISABLED 2026-08-04] 缠论非czsc路由已停用，保留czsc引擎
_CHANLUN_DISABLED_PATHS = ("/api/chanlun/signals", "/api/chanlun/backtest",
    "/api/chanlun/scan", "/api/chanlun/disciplined",
    "/api/chanlun/review", "/api/chanlun/notify")

@app.before_request
def _chanlun_disabled_guard():
    path = request.path
    for dp in _CHANLUN_DISABLED_PATHS:
        if path == dp or path.startswith(dp + "/"):
            # Keep /api/chanlun/czsc* routes active
            if "/czsc" in path:
                return None
            return jsonify({"status": "disabled", "message": "缠论(非czsc)模块已停用"}), 410

@app.before_request
def _track_start():
    request._track_start = _time.time()

@app.after_request
def _track_event(response):
    path = request.path
    if not path.startswith("/api/") or path.startswith("/api/auth/") or path.startswith("/api/analytics"):
        return response
    username = session.get("username", "")
    if not username:
        return response
    try:
        duration = int((_time.time() - getattr(request, '_track_start', _time.time())) * 1000)
        func_name = _classify_function(path)
        with get_db_ctx() as conn:
            conn.execute(
                "INSERT INTO user_events (user_id, event_time, function_name, method, path, status_code, duration_ms) VALUES (?, datetime('now'), ?, ?, ?, ?, ?)",
                (username, func_name, request.method, path, response.status_code, duration)
            )
            conn.commit()
    except Exception:
        pass
    _cleanup_old_events()
    return response

app.register_blueprint(export_bp)
app.register_blueprint(prompts_bp)
app.register_blueprint(compass_bp)
app.register_blueprint(investment_bp)
AGENT_API = "http://localhost:8000"
SHARK_API = "http://49.234.48.221:5000"
COMPASS_API = "http://localhost:8087"
PUBLISHER_API = "http://49.234.48.221:8089"
TMPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

from datafactory.infrastructure.db_utils import DB_PATH, get_db_ctx  # noqa: E402


# === 用户行为事件采集 ===
FUNCTION_MAP = {
    "/api/proxy/tracks/heat": "赛道热度",
    "/api/proxy/tracks": "赛道",
    "/api/news": "资讯",
    "/api/stock/": "个股分析",
    "/api/watchlist": "自选股",
    "/api/report/": "研报",
    "/api/research/": "研报聚合",
    "/api/policy/": "政策分析",
    "/api/weekly/": "周报",
    "/api/user/": "用户设置",
    "/api/content/": "内容创作",
    "/api/prompts": "Prompt管理",
    "/api/tasks": "采集任务",
    "/api/meta": "元数据",
    "/api/service-status": "服务状态",
    "/api/push/": "推送配置",
    "/api/notify/": "通知",
    "/api/llm-config": "LLM配置",
    "/api/keyword-": "关键词",
    "/api/proxy/recommendation": "股票推荐",
}


def _init_monitor_tables():
    with get_db_ctx() as conn:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS monitor_rules ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "type TEXT NOT NULL, "
            "config_json TEXT NOT NULL, "
            "severity TEXT NOT NULL DEFAULT 'warning', "
            "enabled INTEGER NOT NULL DEFAULT 1, "
            "builtin INTEGER NOT NULL DEFAULT 0, "
            "interval_sec INTEGER NOT NULL DEFAULT 60, "
            "created_at DATETIME DEFAULT (datetime('now'))"
            "); "
            "CREATE TABLE IF NOT EXISTS monitor_results ("
            "rule_id INTEGER NOT NULL, "
            "status TEXT NOT NULL, "
            "message TEXT, "
            "detail_json TEXT, "
            "checked_at DATETIME DEFAULT (datetime('now'))"
            ")"
        )
        count = conn.execute("SELECT count(*) FROM monitor_rules WHERE builtin=1").fetchone()[0]
        if count == 0:
            builtin_rules = [
                ("小红书 Cookie 有效性", "custom", json.dumps({"url": PUBLISHER_API + "/api/cookie/validate?mode=fast", "judge": "valid", "timeout": 10, "status_url": PUBLISHER_API + "/api/cookie/status"}), "critical", 120),
                ("Ghost Browser CDP 连通性", "http", json.dumps({"url": "http://localhost:9222/json/version", "timeout": 5}), "critical", 60),
                ("发布锁状态", "system", json.dumps({"check": "file_not_exists", "path": "/tmp/d8q_publishing.lock"}), "warning", 30),
                ("发布服务健康", "http", json.dumps({"url": PUBLISHER_API + "/api/health", "timeout": 10}), "critical", 120),
            ]
            for name, rtype, cfg, sev, interval in builtin_rules:
                conn.execute("INSERT INTO monitor_rules (name,type,config_json,severity,enabled,builtin,interval_sec) VALUES (?,?,?,?,1,1,?)",
                            (name, rtype, cfg, sev, interval))
            conn.commit()


def _classify_function(path):
    for prefix in sorted(FUNCTION_MAP.keys(), key=len, reverse=True):
        if path.startswith(prefix):
            return FUNCTION_MAP[prefix]
    return "其他"

def _init_events_table():
    with get_db_ctx() as conn:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS user_events ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id TEXT NOT NULL, "
            "event_time DATETIME NOT NULL, "
            "function_name TEXT NOT NULL, "
            "method TEXT, "
            "path TEXT, "
            "status_code INTEGER, "
            "duration_ms INTEGER"
            "); "
            "CREATE INDEX IF NOT EXISTS idx_ue_user_time ON user_events(user_id, event_time); "
            "CREATE INDEX IF NOT EXISTS idx_ue_func_time ON user_events(function_name, event_time);"
        )
        conn.commit()


def _init_alert_tables():
    """初始化智能预警中心表"""
    with get_db_ctx() as conn:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS alert_rules ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id TEXT NOT NULL, "
            "rule_type TEXT NOT NULL, "
            "rule_name TEXT NOT NULL, "
            "condition_json TEXT NOT NULL, "
            "severity TEXT NOT NULL DEFAULT 'normal', "
            "enabled INTEGER NOT NULL DEFAULT 1, "
            "cooldown_hours INTEGER NOT NULL DEFAULT 4, "
            "created_at DATETIME DEFAULT (datetime('now')), "
            "last_triggered_at DATETIME"
            "); "
            "CREATE TABLE IF NOT EXISTS alerts ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id TEXT NOT NULL, "
            "rule_id INTEGER, "
            "alert_type TEXT NOT NULL, "
            "severity TEXT NOT NULL DEFAULT 'normal', "
            "title TEXT NOT NULL, "
            "message TEXT, "
            "context_json TEXT, "
            "is_read INTEGER NOT NULL DEFAULT 0, "
            "created_at DATETIME DEFAULT (datetime('now'))"
            "); "
            "CREATE INDEX IF NOT EXISTS idx_alert_rules_user ON alert_rules(user_id, enabled); "
            "CREATE INDEX IF NOT EXISTS idx_alerts_user_unread ON alerts(user_id, is_read, created_at);"
        )
        # 默认规则: 为admin创建4条
        count = conn.execute("SELECT count(*) FROM alert_rules WHERE user_id='admin'").fetchone()[0]
        if count == 0:
            import json as _json
            default_rules = [
                ("track_heat", "赛道热度预警", _json.dumps({"metric": "heat_score", "operator": ">", "threshold": 80, "track_name": "全部"}), "normal"),
                ("funding", "融资金额预警", _json.dumps({"metric": "amount", "operator": ">", "threshold": 10000, "unit": "万元"}), "normal"),
                ("policy", "重大政策预警", _json.dumps({"keywords": ["重大", "突发", "紧急"], "level": "national"}), "urgent"),
                ("stock_score", "个股评分变化预警", _json.dumps({"metric": "score_change", "operator": ">", "threshold": 10}), "normal"),
            ]
            for rule_type, rule_name, condition, severity in default_rules:
                conn.execute(
                    "INSERT INTO alert_rules (user_id, rule_type, rule_name, condition_json, severity) VALUES (?,?,?,?,?)",
                    ("admin", rule_type, rule_name, condition, severity)
                )
            conn.commit()



def _init_score_history_table():
    """初始化自选股评分历史表"""
    with get_db_ctx() as conn:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS score_history ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "stock_code TEXT NOT NULL, "
            "stock_name TEXT, "
            "date TEXT NOT NULL, "
            "total_score REAL, "
            "technical_score REAL, "
            "trend_score REAL, "
            "fundamental_score REAL, "
            "volume_score REAL, "
            "signal TEXT, "
            "risk_level TEXT, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "UNIQUE(stock_code, date)"
            "); "
            "CREATE INDEX IF NOT EXISTS idx_sh_code_date ON score_history(stock_code, date DESC); "
            "CREATE INDEX IF NOT EXISTS idx_sh_date ON score_history(date);"
        )
        conn.commit()


def _init_portfolio_tables():
    with get_db_ctx() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                initial_capital REAL DEFAULT 1000000,
                cash REAL DEFAULT 1000000,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL DEFAULT '',
                quantity INTEGER DEFAULT 0,
                avg_cost REAL DEFAULT 0,
                current_price REAL DEFAULT 0,
                updated_at DATETIME DEFAULT (datetime('now')),
                UNIQUE(portfolio_id, stock_code)
            );
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL DEFAULT '',
                direction TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                amount REAL NOT NULL,
                trade_date TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS net_value_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                net_value REAL NOT NULL DEFAULT 1.0,
                total_assets REAL NOT NULL DEFAULT 0,
                UNIQUE(portfolio_id, date)
            );
            CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);
            CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id);
            CREATE INDEX IF NOT EXISTS idx_trades_portfolio ON trades(portfolio_id);
            CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date);
            CREATE INDEX IF NOT EXISTS idx_net_value_portfolio_date ON net_value_history(portfolio_id, date);
        """)
        conn.commit()



def _init_followed_investors_table():
    with get_db_ctx() as conn:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS followed_investors ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id TEXT NOT NULL, "
            "investor_name TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "UNIQUE(user_id, investor_name)"
            "); "
            "CREATE INDEX IF NOT EXISTS idx_fi_user ON followed_investors(user_id);"
        )
        conn.commit()

def _init_rec_history_table():
    with get_db_ctx() as conn:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS recommendation_history ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "rec_date TEXT NOT NULL, "
            "stock_code TEXT NOT NULL, "
            "stock_name TEXT, "
            "rec_score REAL, "
            "technical_score REAL, "
            "trend_score REAL, "
            "fundamental_score REAL, "
            "volume_score REAL, "
            "price_at_rec REAL, "
            "price_t1 REAL, price_t3 REAL, price_t5 REAL, price_t10 REAL, "
            "return_t1 REAL, return_t3 REAL, return_t5 REAL, return_t10 REAL, "
            "benchmark_t5 REAL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "UNIQUE(rec_date, stock_code)"
            "); "
            "CREATE INDEX IF NOT EXISTS idx_rh_date ON recommendation_history(rec_date DESC); "
            "CREATE INDEX IF NOT EXISTS idx_rh_code ON recommendation_history(stock_code, rec_date DESC);"
        )
        conn.commit()

try:
    _init_events_table()
    _init_monitor_tables()
    _init_alert_tables()
    _init_score_history_table()
    _init_portfolio_tables()
    _init_rec_history_table()
    _init_followed_investors_table()
except Exception:
    pass

_last_cleanup_date = ""
def _cleanup_old_events():
    global _last_cleanup_date
    from datetime import date as _date
    today = str(_date.today())
    if _last_cleanup_date == today:
        return
    _last_cleanup_date = today
    try:
        with get_db_ctx() as conn:
            conn.execute("DELETE FROM user_events WHERE event_time < datetime('now', '-90 days')")
            conn.commit()
    except Exception:
        pass


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
            return {"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


@app.route("/")
@app.route("/track")
@app.route("/feed")
@app.route("/weekly")
@app.route("/tasks")
@app.route("/stock")
@app.route("/report")
@app.route("/settings")
@app.route("/policy")
@app.route("/follows")
@app.route("/monitor")
@app.route("/recommend")
def index():
    with open(os.path.join(TMPL_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/stock/<code>")
def stock_detail(code):
    """Serve SPA shell for stock detail page — frontend router handles the rest."""
    with open(os.path.join(TMPL_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/api/proxy/tracks", methods=["GET"])
@app.route("/api/proxy/tracks/heat", methods=["GET"])
@app.route("/api/proxy/tracks/heat/latest", methods=["GET"])
@app.route("/api/proxy/tracks/<int:track_id>/news", methods=["GET"])
@app.route("/api/proxy/tracks/<int:track_id>/keywords", methods=["GET"])
def proxy_tracks(**kwargs):
    """Proxy track API to Agent"""
    path = request.path.replace("/api/proxy/", "/api/")
    qs = request.query_string.decode()
    url = AGENT_API + path + ("?" + qs if qs else "")
    # Inject user_id for personalization (unless admin requests view=all, or user has no subscriptions)
    _username = session.get("username", "")
    _role = session.get("role", "viewer")
    if _username and request.args.get("view") != "all":
        # Check if user has any subscriptions
        with get_db_ctx() as _conn:
            _has_subs = _conn.execute("SELECT 1 FROM user_subscriptions WHERE user_id=? LIMIT 1", (_username,)).fetchone()
        if _has_subs:
            sep = "&" if "?" in url else "?"
            url = url + sep + "user_id=" + urllib.parse.quote(_username)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json as _json
            return _json.loads(resp.read()), resp.status
    except Exception as e:
        return {"error": str(e)}, 502


@app.route("/api/proxy/tracks/<int:track_id>/keywords", methods=["POST"])
@app.route("/api/proxy/tracks/<int:track_id>/keywords/<path:keyword>", methods=["DELETE"])
def proxy_tracks_keywords_write(track_id, keyword=None):
    if session.get("role") != "admin":
        return {"error": "仅管理员可管理关键词"}, 403
    if request.method == "POST":
        path = f"/api/tracks/{track_id}/keywords"
        url = AGENT_API + path
        data = json.dumps(request.json or {}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        kw_enc = urllib.parse.quote(keyword, safe="")
        url = AGENT_API + f"/api/tracks/{track_id}/keywords/{kw_enc}"
        req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return json.loads(body), e.code
        except Exception:
            return {"error": body.decode()[:200]}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


@app.route("/api/weekly/generate", methods=["POST"])
def weekly_generate():
    """Generate weekly report via LLM"""
    from datafactory.content.llm_creator import _llm_call, _fetch_news
    body = request.json or {}
    track_id = body.get("track_id", 1)
    days = body.get("days", 7)
    with get_db_ctx() as conn:
        track = conn.execute("SELECT name FROM tracks WHERE id=?", (track_id,)).fetchone()
    if not track:
        return jsonify({"error": "赛道不存在"}), 404
    track_name = track["name"]
    news = _fetch_news(track_name, days)
    if not news:
        return jsonify({"error": "无资讯数据"}), 404
    news_text = "\n".join("- [" + n["title"] + "] (" + n.get("source","") + ", " + (n.get("publish_time",""))[:10] + ")" for n in news[:20])
    # 从 prompt 配置加载
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from prompt_loader import PromptManager as _PM
    _pm = _PM(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts'))
    _wk_cfg = _pm.get('weekly_report') or {}
    _wk_system = _wk_cfg.get('system', '你是资深行业分析师。')
    _wk_template = _wk_cfg.get('template', '你是专业的投资分析师。根据以下资讯，生成一份结构化的行业周报。')
    prompt = _wk_template + f"""

赛道：{track_name}
时间范围：近{days}天
资讯列表：
{news_text}

要求：
1. 分为：本周概览、重要事件、政策动态、融资并购、机构观点、下周关注
2. 每个章节用 ## 标题
3. 要点用 • 列表
4. 总字数 800-1200 字
5. 语气专业客观"""
    try:
        content = _llm_call(prompt, system=_wk_system)
        return jsonify({"content": content, "track": track_name, "news_count": len(news)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- News API ---
@app.route("/api/meta")
def meta():
    with get_db_ctx() as conn:
        subjects = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM financial_news ORDER BY subject")]
        sources = [r[0] for r in conn.execute("SELECT DISTINCT source FROM financial_news ORDER BY source")]
        # Subject 校验过滤：排除测试标记、非法 subject、特殊值和纯 ASCII 短串
        _test_re = re.compile(r'^(压力测试|并发测试|存储测试|AI并发测试)', re.IGNORECASE)
        _ctrl_re = re.compile(r"[\x00-\x1f\x7f-\x9f]")
        _garbage_re = re.compile(r'^(|-)?(Inf(inity)?|NaN|NIL|None|null|undefined)$', re.IGNORECASE)
        _cjk_re = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
        subjects = [s for s in subjects if isinstance(s, str)
                    and 2 <= len(s) <= 50
                    and not _ctrl_re.search(s)
                    and not _test_re.search(s)
                    and not _garbage_re.match(s)
                    and (_cjk_re.search(s) or len(s) >= 4)]
        return jsonify({"subjects": subjects, "sources": sources})


@app.route("/api/news")
def news():
    page = int(request.args.get("page", 1))
    size = min(int(request.args.get("size", 10)), 50)
    subject = request.args.get("subject", "")
    source = request.args.get("source", "")
    date = request.args.get("date", "")
    keyword = request.args.get("keyword", "")
    news_type = request.args.get("news_type", "")
    where, params = [], []
    if subject:
        where.append("subject=?")
        params.append(subject)
    if source:
        where.append("source=?")
        params.append(source)
    if date:
        where.append("DATE(publish_time)=?")
        params.append(date)
    if keyword:
        where.append("(title LIKE ? OR entities LIKE ?)")
        params.extend(['%'+keyword+'%', '%'+keyword+'%'])
    if news_type:
        where.append("news_type=?")
        params.append(news_type)
    # User subscription filtering
    _news_username = session.get("username", "")
    _news_role = session.get("role", "viewer")
    _news_view = request.args.get("view", "")
    if _news_username and _news_view != "all":
        with get_db_ctx() as conn_u:
            _sub_rows = conn_u.execute(
                "SELECT t.name FROM user_subscriptions us JOIN tracks t ON us.track_id = t.id WHERE us.user_id = ?",
                (_news_username,)
            ).fetchall()
        if _sub_rows:
            _track_names = [r[0] for r in _sub_rows]
            _placeholders = ",".join(["?"] * len(_track_names))
            where.append(f"subject IN ({_placeholders})")
            params.extend(_track_names)
        # If no subscriptions, return full data (new user guidance)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    with get_db_ctx() as conn:
        total = conn.execute("SELECT count(*) FROM financial_news" + clause, params).fetchone()[0]
        subjects_count = conn.execute("SELECT count(DISTINCT subject) FROM financial_news" + clause, params).fetchone()[0]
        sources_count = conn.execute("SELECT count(DISTINCT source) FROM financial_news" + clause, params).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM financial_news" + clause + " ORDER BY publish_time DESC LIMIT ? OFFSET ?",
            params + [size, (page - 1) * size]).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            d.pop("metadata", None)
            d.pop("file_path", None)
            items.append(d)
        return jsonify({"total": total, "subjects": subjects_count, "sources": sources_count, "items": items, "page": page, "size": size})


# --- Task API (proxy to agent) ---
@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    data, code = agent_request("GET", "/api/tasks")
    return jsonify(data), code


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data, code = agent_request("POST", "/api/tasks", request.json)
    return jsonify(data), code


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    data, code = agent_request("PUT", "/api/tasks/" + task_id, request.json)
    return jsonify(data), code


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    data, code = agent_request("DELETE", "/api/tasks/" + task_id)
    return jsonify(data), code


@app.route("/api/tasks/<task_id>/run", methods=["POST"])
def run_task(task_id):
    data, code = agent_request("POST", "/api/tasks/" + task_id + "/run")
    return jsonify(data), code



@app.route("/api/tasks/<task_id>/toggle", methods=["PUT"])
def toggle_task(task_id):
    data, code = agent_request("PUT", "/api/tasks/" + task_id + "/toggle")
    return jsonify(data), code


def _publisher_request(method, path, data=None, max_retries=1):
    """Proxy request to InfoPublisher API (with retry on 500/502)"""
    url = PUBLISHER_API + path
    body = json.dumps(data).encode() if data else None
    last_result = None
    last_code = 502
    for attempt in range(max_retries + 1):
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read()), resp.status
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                last_result = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                last_result = {"error": f"publisher returned HTTP {e.code}: {raw[:200]}"}
            last_code = e.code
            # Only retry on server errors (500/502/503), not client errors
            if e.code < 500 or attempt >= max_retries:
                return last_result, last_code
            logger.info("publisher %s retry %d/%d (HTTP %d)", path, attempt+1, max_retries, e.code)
            _time.sleep(3 * (attempt + 1))
        except Exception as e:
            last_result = {"error": str(e)}
            last_code = 502
            if attempt >= max_retries:
                return last_result, last_code
            logger.info("publisher %s retry %d/%d (%s)", path, attempt+1, max_retries, str(e)[:60])
            _time.sleep(3 * (attempt + 1))
    return last_result, last_code




class ReportCache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if entry is None:
            return None
        if _time.time() > entry["expire_at"]:
            del self._store[key]
            return None
        return entry["data"]

    def set(self, key, data, ttl_seconds):
        self._store[key] = {"data": data, "expire_at": _time.time() + ttl_seconds}

    def get_or_fetch(self, key, fetch_fn, ttl_seconds):
        cached = self.get(key)
        if cached is not None:
            return cached, True
        data = fetch_fn()
        self.set(key, data, ttl_seconds)
        return data, False

    def stats(self):
        now = _time.time()
        active = sum(1 for e in self._store.values() if e["expire_at"] > now)
        return {"active": active, "total_entries": len(self._store)}

_report_cache = ReportCache()

def shark_request(method, path, data=None):
    """Proxy request to StockShark API"""
    url = SHARK_API + urllib.parse.quote(path, safe='/:?=&')
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return json.loads(_raw), e.code
        except (json.JSONDecodeError, ValueError):
            return {"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


def compass_request(method, path, data=None):
    """Proxy request to Compass API"""
    url = COMPASS_API + urllib.parse.quote(path, safe='/:?=&')
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
            return {"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


# 股票名称/代码互转缓存
_stock_cache = {}

def resolve_stock(input_str):
    """将股票名称或代码统一解析为 (code, name)，使用东方财富搜索"""
    input_str = input_str.strip()
    if not input_str:
        return input_str, input_str
    if input_str in _stock_cache:
        return _stock_cache[input_str]
    # 纯6位数字直接视为代码
    if input_str.isdigit() and len(input_str) == 6:
        _stock_cache[input_str] = (input_str, input_str)
        return input_str, input_str
    # 用东方财富 suggest 接口解析名称→代码
    try:
        url = "https://searchapi.eastmoney.com/api/suggest/get?input=" + urllib.parse.quote(input_str) + "&type=14&count=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        items = data.get("QuotationCodeTable", {}).get("Data", [])
        if items:
            code = items[0].get("Code", input_str)
            name = items[0].get("Name", input_str)
            result = (code, name)
            _stock_cache[input_str] = result
            return result
    except Exception:
        pass
    _stock_cache[input_str] = (input_str, input_str)
    return input_str, input_str


# --- Stock Analysis API (proxy to StockShark) ---
@app.route("/api/stock/comprehensive", methods=["POST"])
def stock_comprehensive():
    data, code = shark_request("POST", "/api/analysis/stock/comprehensive", request.json)
    return jsonify(data), code


@app.route("/api/stock/announcements", methods=["GET"])
def stock_announcements():
    sc = request.args.get("stock_code", "")
    days = request.args.get("days", "30")
    ai = request.args.get("ai_summary", "false").lower() == "true"
    code, name = resolve_stock(sc)
    data, status = shark_request("GET", "/api/announcement/stock/" + code + "?days=" + days)
    if status == 200 and ai and data.get("announcements"):
        from datafactory.content.llm_creator import _llm_call
        titles = [a["title"] for a in data["announcements"][:10]]
        prompt = "以下是上市公司近期公告标题列表，请用1-2句话概括核心要点和对投资者的影响：\n" + "\n".join(f"- {t}" for t in titles)
        try:
            data["ai_summary"] = _llm_call(prompt, system="你是证券分析师，简洁专业地解读公告。")
        except Exception:
            data["ai_summary"] = None
    return jsonify(data), status

@app.route("/api/stock/reports", methods=["GET"])
def stock_reports():
    keyword = request.args.get("keyword", "")
    limit = request.args.get("limit", "20")
    cache_key = "report:" + keyword + ":" + limit
    def fetch():
        data, status = shark_request("GET", "/api/report/search?keyword=" + keyword + "&limit=" + limit)
        return (data, status) if status == 200 else None
    cached = _report_cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    data, status = shark_request("GET", "/api/report/search?keyword=" + keyword + "&limit=" + limit)
    if status == 200:
        empty = not data.get("reports")
        _report_cache.set(cache_key, data, 300 if empty else 1800)
    return jsonify(data), status


@app.route("/api/stock/quote", methods=["GET"])
def stock_quote():
    symbol = request.args.get("symbol", "")
    code, _ = resolve_stock(symbol)
    data, status = shark_request("GET", "/api/analysis/stock/quote?symbol=" + code)
    return jsonify(data), status





@app.route("/api/stock/valuation", methods=["GET"])
def stock_valuation():
    symbol = request.args.get("symbol", "")
    code, _ = resolve_stock(symbol)
    data, status = shark_request("GET", "/api/analysis/stock/valuation?symbol=" + code)
    return jsonify(data), status


@app.route("/api/stock/financial", methods=["GET"])
def stock_financial():
    symbol = request.args.get("symbol", "")
    report_type = request.args.get("report_type", "annual")
    code, _ = resolve_stock(symbol)
    data, status = shark_request("GET", "/api/analysis/stock/financial?symbol=" + code + "&report_type=" + report_type)
    return jsonify(data), status


@app.route("/api/stock/supply-chain", methods=["GET"])
def stock_supply_chain():
    company = request.args.get("company_name", "")
    if not company:
        return jsonify({"success": False, "error": "missing company_name"}), 400
    data, status = shark_request("GET", "/api/supply-chain/company/supply-chain?company_name=" + company)
    return jsonify(data), status




@app.route("/api/search/by-keyword", methods=["GET"])
def search_by_keyword():
    keyword = request.args.get("keyword", "")
    limit = request.args.get("limit", "20")
    data, status = shark_request("GET", "/api/search/stock/by-keyword?keyword=" + keyword + "&limit=" + limit)
    return jsonify(data), status


# --- Compass Recommendation Proxy ---
@app.route("/api/proxy/recommendation/daily", methods=["GET"])
def recommendation_daily():
    """Proxy daily stock recommendation from Compass."""
    data, code = compass_request("GET", "/api/recommendation/daily")
    return jsonify(data), code


@app.route("/api/proxy/recommendation/generate", methods=["POST"])
def recommendation_generate():
    """Trigger recommendation generation via Compass (admin only)."""
    if session.get("role") != "admin":
        return jsonify({"error": "仅管理员可操作"}), 403
    data, code = compass_request("POST", "/api/recommendation/generate", request.json)
    return jsonify(data), code


@app.route("/api/search/by-industry", methods=["GET"])
def search_by_industry():
    qs = request.query_string.decode() if request.query_string else ""
    data, status = shark_request("GET", "/api/search/stock/by-industry?" + qs)
    return jsonify(data), status


@app.route("/api/search/by-concept", methods=["GET"])
def search_by_concept():
    qs = request.query_string.decode() if request.query_string else ""
    data, status = shark_request("GET", "/api/search/stock/by-concept?" + qs)
    return jsonify(data), status


@app.route("/api/search/by-theme", methods=["GET"])
def search_by_theme():
    qs = request.query_string.decode() if request.query_string else ""
    data, status = shark_request("GET", "/api/search/stock/by-theme?" + qs)
    return jsonify(data), status


@app.route("/api/search/industries", methods=["GET"])
def list_industries():
    data, status = shark_request("GET", "/api/search/industries")
    return jsonify(data), status


@app.route("/api/search/concepts", methods=["GET"])
def list_concepts():
    data, status = shark_request("GET", "/api/search/concepts")
    return jsonify(data), status


@app.route("/api/search/concepts/summary", methods=["GET"])
def list_concepts_summary():
    limit = request.args.get("limit", "30")
    data, status = shark_request("GET", f"/api/search/concepts/summary?limit={limit}")
    return jsonify(data), status


@app.route("/api/search/sectors", methods=["GET"])
def list_sectors():
    limit = request.args.get("limit", "20")
    data, status = shark_request("GET", f"/api/search/industries/summary?limit={limit}")
    return jsonify(data), status

@app.route("/api/search/industries/summary", methods=["GET"])
def list_industries_summary():
    limit = request.args.get("limit", "20")
    data, status = shark_request("GET", f"/api/search/industries/summary?limit={limit}")
    return jsonify(data), status


@app.route("/api/report/stock", methods=["POST"])
def report_stock_query():
    """批量查询股票研报 - 缓存优先，减少远端调用"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    body = request.json or {}
    keywords = body.get("keywords", [])[:20]
    days = body.get("days", 7)

    results = [None] * len(keywords)
    cache_hits = 0

    # Phase 1: check cache for each keyword
    missed_indices = []
    for i, kw in enumerate(keywords):
        rpt_key = "report:" + kw + ":20"
        code, name = resolve_stock(kw)
        ann_key = "announcement:" + code + ":" + str(days)
        rpt_cached = _report_cache.get(rpt_key)
        ann_cached = _report_cache.get(ann_key)
        if rpt_cached is not None and ann_cached is not None:
            results[i] = {
                "stock_code": code,
                "stock_name": name,
                "reports": rpt_cached,
                "announcements": ann_cached,
            }
            cache_hits += 1
        else:
            missed_indices.append((i, kw, code, name, rpt_key, ann_key, rpt_cached, ann_cached))

    # Phase 2: fetch missed items (partial cache supported)
    def _fetch_one(idx, kw, code, name, rpt_key, ann_key, rpt_cached, ann_cached):
        if rpt_cached is None:
            rpt_data, rpt_code = shark_request("GET", "/api/report/search?keyword=" + kw + "&limit=20")
            reports = rpt_data.get("reports", []) if rpt_code == 200 else []
            empty = not reports
            _report_cache.set(rpt_key, reports, 300 if empty else 1800)
        else:
            reports = rpt_cached
        if ann_cached is None:
            ann_data, ann_code = shark_request("GET", "/api/announcement/stock/" + code + "?days=" + str(days))
            anns = ann_data.get("announcements", []) if ann_code == 200 else []
            _report_cache.set(ann_key, anns, 300 if not anns else 900)
        else:
            anns = ann_cached
        return idx, {"stock_code": code, "stock_name": name, "reports": reports, "announcements": anns}

    if missed_indices:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(_fetch_one, *args) for args in missed_indices]
            for f in as_completed(futures):
                idx, result = f.result()
                results[idx] = result

    resp = jsonify({"results": results})
    resp.headers["X-Cache-Hits"] = str(cache_hits) + "/" + str(len(keywords))
    return resp, 200



# --- Content Creation API ---
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

ARTICLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles")


@app.route("/api/content/create", methods=["POST"])
def content_create():
    """手动触发内容创作"""
    from datafactory.content.creator import create_article
    body = request.json or {}
    subject = body.get("subject", "")
    style = body.get("style", "news_brief")
    freq = body.get("freq", "daily")
    if not subject:
        return jsonify({"error": "subject必填"}), 400
    result = create_article(subject, style=style, freq=freq)
    return jsonify(result), 200


@app.route("/api/content/articles", methods=["GET"])
def content_articles():
    """查看已生成的文章列表"""
    articles = []
    if os.path.exists(ARTICLES_DIR):
        for subject in sorted(os.listdir(ARTICLES_DIR)):
            sp = os.path.join(ARTICLES_DIR, subject)
            if not os.path.isdir(sp):
                continue
            for date_dir in sorted(os.listdir(sp), reverse=True):
                dp = os.path.join(sp, date_dir)
                if not os.path.isdir(dp):
                    continue
                for f in sorted(os.listdir(dp)):
                    if f.endswith(".md"):
                        fp = os.path.join(dp, f)
                        articles.append({
                            "subject": subject,
                            "date": date_dir,
                            "filename": f,
                            "path": os.path.relpath(fp, ARTICLES_DIR),
                            "size": os.path.getsize(fp),
                        })
    return jsonify({"articles": articles, "total": len(articles)}), 200


@app.route("/api/content/article", methods=["GET"])
def content_article_read():
    """读取文章内容"""
    path = request.args.get("path", "")
    fp = os.path.join(ARTICLES_DIR, path)
    if not os.path.exists(fp) or not fp.startswith(ARTICLES_DIR):
        return jsonify({"error": "文章不存在"}), 404
    with open(fp, "r", encoding="utf-8") as f:
        return jsonify({"content": f.read(), "path": path}), 200


# --- Creation/Publish Task Scheduler ---
TASK_STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "content_tasks.json")


def _load_content_tasks():
    if os.path.exists(TASK_STORE_PATH):
        with open(TASK_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_content_tasks(tasks):
    os.makedirs(os.path.dirname(TASK_STORE_PATH), exist_ok=True)
    with open(TASK_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

EXEC_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exec_log.json")

def _append_exec_log(task, result, duration, trigger="manual"):
    import fcntl
    entry = {
        "task_id": task.get("id", ""),
        "type": task.get("type", ""),
        "subject": task.get("subject", ""),
        "trigger": trigger,
        "success": "error" not in result and result.get("status") != "error",
        "result_summary": result.get("error") or result.get("title") or result.get("status") or str(result)[:100],
        "duration": round(duration, 1),
        "time": __import__("datetime").datetime.now().isoformat()
    }
    try:
        with open(EXEC_LOG_PATH, "r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            logs = __import__("json").load(f)
            logs.insert(0, entry)
            logs = logs[:200]  # keep last 200
            f.seek(0)
            f.truncate()
            __import__("json").dump(logs, f, ensure_ascii=False, indent=2)
    except (FileNotFoundError, __import__("json").JSONDecodeError):
        with open(EXEC_LOG_PATH, "w", encoding="utf-8") as f:
            __import__("json").dump([entry], f, ensure_ascii=False, indent=2)



@app.route("/api/content/tasks", methods=["GET"])
def list_content_tasks():
    return jsonify(_load_content_tasks()), 200


@app.route("/api/content/tasks", methods=["POST"])
def create_content_task():
    import uuid
    body = request.json or {}
    body["id"] = str(uuid.uuid4())[:8]
    body["created_at"] = __import__("datetime").datetime.now().isoformat()
    tasks = _load_content_tasks()
    tasks.append(body)
    _save_content_tasks(tasks)
    return jsonify(body), 201


@app.route("/api/content/tasks/<task_id>", methods=["DELETE"])
def delete_content_task(task_id):
    tasks = [t for t in _load_content_tasks() if t.get("id") != task_id]
    _save_content_tasks(tasks)
    return jsonify({"ok": True}), 200


@app.route("/api/content/tasks/<task_id>", methods=["PUT"])
def update_content_task(task_id):
    body = request.json or {}
    tasks = _load_content_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            for k in ("subject", "style", "channel", "freq", "run_at"):
                if k in body:
                    t[k] = body[k]
            _save_content_tasks(tasks)
            return jsonify(t), 200
    return jsonify({"error": "任务不存在"}), 404


@app.route("/api/content/tasks/<task_id>/toggle", methods=["POST"])
def toggle_content_task(task_id):
    tasks = _load_content_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "active" if t.get("status") == "paused" else "paused"
            _save_content_tasks(tasks)
            return jsonify({"id": task_id, "status": t["status"]}), 200
    return jsonify({"error": "任务不存在"}), 404


@app.route("/api/content/tasks/<task_id>/run", methods=["POST"])
def run_content_task(task_id):
    _t0 = __import__("time").time()
    tasks = _load_content_tasks()
    task = next((t for t in tasks if t.get("id") == task_id), None)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    task_type = task.get("type", "creation")
    if task_type == "creation":
        from datafactory.content.llm_creator import STYLE_CREATORS
        style = task.get("style", "news_brief")
        creator = STYLE_CREATORS.get(style)
        if creator:
            result = creator(task.get("subject", ""), freq=task.get("freq", "daily"))
        else:
            from datafactory.content.creator import create_article
            result = create_article(task.get("subject", ""), style=style, freq=task.get("freq", "daily"))
        _append_exec_log(task, result, __import__("time").time() - _t0, request.args.get("trigger", "manual"))
        return jsonify(result), 200
    elif task_type == "publish":
        # 读取最新文章，调用 infopublisher 服务发布
        subject = task.get("subject", "")
        subject_dir = os.path.join(ARTICLES_DIR, subject)
        if not os.path.exists(subject_dir):
            return jsonify({"error": "无文章可发布"}), 404
        dates = sorted(os.listdir(subject_dir), reverse=True)
        for d in dates:
            dp = os.path.join(subject_dir, d)
            if os.path.isdir(dp):
                files = [f for f in os.listdir(dp) if f.endswith(".md")]
                if files:
                    fp = os.path.join(dp, sorted(files)[-1])
                    with open(fp, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    # 从markdown提取标题和正文
                    lines = md_content.strip().split("\n")
                    title = lines[0].lstrip("# ").strip()[:20] if lines else subject
                    body = "\n".join(ln for ln in lines[1:] if not ln.startswith(">") and ln.strip())[:1000]
                    # 调用 infopublisher API
                    pub_data = {"platform": task.get("channel", "xiaohongshu"), "title": title, "content": body}
                    pub_result, pub_code = _publisher_request("POST", "/api/publish/queue", pub_data, max_retries=0)
                    pub_result["file"] = files[-1]
                    pub_result["subject"] = subject
                    # queued/running 状态不写 exec-log，由 scheduler _poll_pending 统一写入最终结果
                    if pub_result.get("status") not in ("queued", "running"):
                        _append_exec_log(task, pub_result, __import__("time").time() - _t0, request.args.get("trigger", "manual"))
                    else:
                        # 保存 queue_task_id 和 trigger 供 scheduler 轮询后写入 exec-log
                        trigger = request.args.get("trigger", "manual")
                        task["queue_task_id"] = pub_result.get("task_id", "")
                        task["queue_status"] = pub_result["status"]
                        task["queue_trigger"] = trigger
                        _save_content_tasks(tasks)
                    return jsonify(pub_result), 200
        _no_art = {"error": "无文章可发布"}
        _append_exec_log(task, _no_art, __import__("time").time() - _t0, request.args.get("trigger", "manual"))
        return jsonify(_no_art), 404

    return jsonify({"error": "未知任务类型"}), 400





@app.route("/api/content/exec-log", methods=["GET"])
def get_exec_log():
    try:
        with open(EXEC_LOG_PATH, encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        logs = []
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    total = len(logs)
    return jsonify({"total": total, "items": logs[(page-1)*size:page*size], "page": page, "size": size}), 200

@app.route("/api/keyword-suggestions", methods=["GET"])
def keyword_suggestions():
    kw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "keyword_suggestions.json")
    with open(kw_path, encoding="utf-8") as f:
        return jsonify(json.load(f)), 200

@app.route("/api/keyword-suggestions", methods=["PUT"])
def update_keyword_suggestions():
    kw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "keyword_suggestions.json")
    with open(kw_path, "w", encoding="utf-8") as f:
        json.dump(request.json, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "ok"}), 200

# --- LLM内容配置API ---
@app.route("/api/llm-config", methods=["GET"])
def get_llm_config():
    from datafactory.content.llm_config import load_config
    return jsonify(load_config()), 200

@app.route("/api/llm-config", methods=["PUT"])
def update_llm_config():
    from datafactory.content.llm_config import load_config, save_config
    cfg = load_config()
    updates = request.json or {}
    for k, v in updates.items():
        if isinstance(v, dict) and k in cfg:
            cfg[k].update(v)
        else:
            cfg[k] = v
    save_config(cfg)
    return jsonify({"status": "ok"}), 200



# --- 推送配置 API ---
@app.route("/api/push/config", methods=["GET"])
def get_push_config():
    username = session.get("username", "")
    with get_db_ctx() as conn:
        row = conn.execute("SELECT * FROM push_configs WHERE user_id=?", (username,)).fetchone()
    if row:
        return jsonify(dict(row))
    return jsonify({"user_id": username, "email": "", "enabled_types": "[]",
                    "daily_time": "08:00", "weekly_day": "friday", "alert_threshold": 30})


@app.route("/api/push/config", methods=["PUT"])
def update_push_config():
    username = session.get("username", "")
    body = request.json or {}
    with get_db_ctx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO push_configs "
            "(user_id, email, enabled_types, daily_time, weekly_day, alert_threshold, webhook_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, body.get("email", ""), json.dumps(body.get("enabled_types", [])),
             body.get("daily_time", "08:00"), body.get("weekly_day", "friday"),
             body.get("alert_threshold", 30), body.get("webhook_url", "")))
        conn.commit()
    return jsonify({"ok": True})


# --- 服务状态 API (admin only, 读取健康检查结果) ---
@app.route("/api/service-status")
def service_status():
    """实时检测所有微服务状态"""
    import subprocess
    services = {}

    # HTTP 健康检查的服务
    http_services = {
        "agent":         {"port": 8000, "path": "/api/health"},
        "stockshark":    {"host": "49.234.48.221", "port": 5000, "path": "/health"},
        "compass":       {"port": 8087, "path": "/health"},
        "factory":       {"port": 8088, "path": "/"},
        "infopublisher": {"host": "49.234.48.221", "port": 8089, "path": "/api/publish", "method": "GET"},
    }
    for name, cfg in http_services.items():
        try:
            host = cfg.get("host", "localhost")
            url = f"http://{host}:{cfg['port']}{cfg['path']}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5):
                services[name] = {"status": "ok", "type": "http", "port": cfg["port"]}
        except urllib.error.HTTPError as e:
            # 405 = route exists (e.g. POST-only), service is alive
            if e.code == 405:
                services[name] = {"status": "ok", "type": "http", "port": cfg["port"]}
            else:
                services[name] = {"status": "ok" if e.code < 500 else "error", "type": "http", "port": cfg["port"], "code": e.code}
        except Exception:
            services[name] = {"status": "down", "type": "http", "port": cfg["port"]}

    # Ghost Browser 在 49 - 通过 SSH 隧道 (localhost:9222) 检测
    try:
        req = urllib.request.Request("http://localhost:9222/json/version", method="GET")
        with urllib.request.urlopen(req, timeout=5):
            services["ghost_browser"] = {"status": "active", "type": "cdp_tunnel", "cdp": "ok"}
    except Exception:
        services["ghost_browser"] = {"status": "down", "type": "remote_cdp", "cdp": "down"}

    from datetime import datetime
    return jsonify({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "services": services}), 200




# --- 用户订阅 API ---
@app.route("/api/user/subscriptions", methods=["GET"])
def get_user_subscriptions():
    """获取当前用户订阅的赛道"""
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    data, code = agent_request("GET", f"/api/user/{username}/subscriptions")
    return jsonify(data), code

@app.route("/api/user/subscribe", methods=["POST"])
def subscribe_track():
    """订阅赛道"""
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    body = request.json or {}
    body["user_id"] = username
    data, code = agent_request("POST", "/api/user/subscribe", body)
    return jsonify(data), code

@app.route("/api/user/subscribe/<int:track_id>", methods=["DELETE"])
def unsubscribe_track(track_id):
    """取消订阅赛道"""
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    data, code = agent_request("DELETE", f"/api/user/subscribe/{username}/{track_id}")
    return jsonify(data), code

@app.route("/api/user/preferences", methods=["GET"])
def get_user_preferences():
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    data, code = agent_request("GET", f"/api/user/{username}/preferences")
    return jsonify(data), code

@app.route("/api/user/preferences", methods=["PUT"])
def set_user_preference():
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    body = request.json or {}
    body["user_id"] = username
    data, code = agent_request("PUT", "/api/user/preferences", body)
    return jsonify(data), code


# --- 自选股 API (proxy to Agent) ---
@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    data, code = agent_request("GET", f"/api/user/{username}/watchlist")
    return jsonify(data), code


@app.route("/api/watchlist", methods=["POST"])
def add_watchlist():
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    body = request.json or {}
    body["user_id"] = username
    data, code = agent_request("POST", "/api/user/watchlist", body)
    return jsonify(data), code


@app.route("/api/watchlist/<stock_code>", methods=["DELETE"])
def del_watchlist(stock_code):
    username = session.get("username", "")
    if not username:
        return jsonify({"success": False, "error": "未登录"}), 401
    data, code = agent_request("DELETE", f"/api/user/{username}/watchlist/{stock_code}")
    return jsonify(data), code


# --- 赛道研报聚合 + AI观点汇总 ---
@app.route("/api/research/track/<int:track_id>", methods=["GET"])
def research_by_track(track_id):
    """按赛道聚合研报 + AI观点汇总（带日级缓存）"""
    from datetime import datetime
    refresh = request.args.get("refresh") == "1"
    today = datetime.now().strftime("%Y-%m-%d")

    with get_db_ctx() as conn:
        track = conn.execute("SELECT name, keywords FROM tracks WHERE id=?", (track_id,)).fetchone()
        if not track:
            return jsonify({"error": "赛道不存在"}), 404

        # 检查缓存（同一赛道同一天只调一次LLM）
        cache = None
        if not refresh:
            cache = conn.execute(
                "SELECT data FROM research_cache WHERE track_id=? AND date=?",
                (track_id, today)).fetchone()

    if cache:
        result = json.loads(cache["data"])
        result["cached"] = True
        return jsonify(result)

    keywords = json.loads(track["keywords"])
    all_reports = []
    for kw in keywords[:3]:
        data, code = shark_request("GET", "/api/report/search?keyword=" + urllib.parse.quote(kw) + "&limit=10")
        if code == 200 and isinstance(data, dict):
            all_reports.extend(data.get("reports", data.get("results", [])))

    seen = set()
    unique = []
    for r in all_reports:
        title = r.get("title", "")
        if title not in seen:
            seen.add(title)
            unique.append(r)

    result = {"track": track["name"], "reports": unique[:15], "total": len(unique), "date": today}

    if unique:
        from datafactory.content.llm_creator import _llm_call
        titles = "\n".join("- " + r.get("title", "") + " (" + r.get("org", r.get("source", "")) + ")" for r in unique[:10])
        try:
            summary = _llm_call(
                f"以下是关于「{track['name']}」赛道的最新研报列表，请用3-5句话总结机构的整体观点倾向（看多/看空/共识），不要逐条列举：\n{titles}",
                system="你是专业的投资分析师，擅长提炼研报观点。"
            )
            result["ai_summary"] = summary
        except Exception:
            result["ai_summary"] = None

    # 写入缓存
    with get_db_ctx() as conn:
        conn.execute("INSERT OR REPLACE INTO research_cache (track_id, date, data) VALUES (?,?,?)",
                    (track_id, today, json.dumps(result, ensure_ascii=False)))
        conn.commit()
    result["cached"] = False
    return jsonify(result)

# --- 运营分析 API (admin only) ---
@app.route("/api/analytics/overview")
def analytics_overview():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    with get_db_ctx() as conn:
        dau = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_events WHERE DATE(event_time)=DATE('now')").fetchone()[0]
        mau = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_events WHERE event_time >= datetime('now', '-30 days')").fetchone()[0]
        today_events = conn.execute("SELECT COUNT(*) FROM user_events WHERE DATE(event_time)=DATE('now')").fetchone()[0]
        top = conn.execute("SELECT function_name, COUNT(*) as c FROM user_events WHERE DATE(event_time)=DATE('now') GROUP BY function_name ORDER BY c DESC LIMIT 1").fetchone()
        return jsonify({"dau": dau, "mau": mau, "today_events": today_events,
            "top_function": {"name": top[0], "count": top[1]} if top else {"name": "-", "count": 0}})

@app.route("/api/analytics/functions")
def analytics_functions():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    with get_db_ctx() as conn:
        cutoff = "datetime('now', '-{} days')".format(days) if days < 9999 else "datetime('2000-01-01')"
        total = conn.execute("SELECT COUNT(*) FROM user_events WHERE event_time >= " + cutoff).fetchone()[0]
        rows = conn.execute("SELECT function_name, COUNT(*) as c FROM user_events WHERE event_time >= " + cutoff + " GROUP BY function_name ORDER BY c DESC").fetchall()
        return jsonify({"functions": [{"name": r[0], "count": r[1], "percentage": round(r[1]/max(total,1)*100, 1)} for r in rows], "total": total})

@app.route("/api/analytics/users")
def analytics_users():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    with get_db_ctx() as conn:
        cutoff = "datetime('now', '-{} days')".format(days) if days < 9999 else "datetime('2000-01-01')"
        rows = conn.execute("SELECT user_id, MAX(event_time) as last_active, COUNT(DISTINCT function_name) as func_count, COUNT(*) as total_calls, ROUND(CAST(COUNT(*) AS FLOAT) / MAX(julianday('now') - julianday(MIN(event_time)), 1), 1) as daily_avg FROM user_events WHERE event_time >= " + cutoff + " GROUP BY user_id ORDER BY total_calls DESC").fetchall()
        return jsonify({"users": [{"user_id": r[0], "last_active": r[1], "function_count": r[2], "total_calls": r[3], "daily_avg": r[4]} for r in rows]})

@app.route("/api/analytics/trends")
def analytics_trends():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    with get_db_ctx() as conn:
        rows = conn.execute("SELECT DATE(event_time) as date, COUNT(DISTINCT user_id) as dau, COUNT(*) as total_calls FROM user_events WHERE event_time >= datetime('now', '-{} days') GROUP BY DATE(event_time) ORDER BY date".format(days)).fetchall()
        return jsonify({"trends": [{"date": r[0], "dau": r[1], "total_calls": r[2]} for r in rows]})

@app.route("/api/analytics/cold-hot")
def analytics_cold_hot():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    with get_db_ctx() as conn:
        users = [r[0] for r in conn.execute("SELECT DISTINCT user_id FROM user_events WHERE event_time >= datetime('now', '-{} days') ORDER BY user_id".format(days)).fetchall()]
        functions = [r[0] for r in conn.execute("SELECT DISTINCT function_name FROM user_events WHERE event_time >= datetime('now', '-{} days') ORDER BY function_name".format(days)).fetchall()]
        user_idx = {u: i for i, u in enumerate(users)}
        func_idx = {f: i for i, f in enumerate(functions)}
        matrix = [[0] * len(functions) for _ in range(len(users))]
        rows = conn.execute("SELECT user_id, function_name, COUNT(*) as c FROM user_events WHERE event_time >= datetime('now', '-{} days') GROUP BY user_id, function_name".format(days)).fetchall()
        for r in rows:
            if r[0] in user_idx and r[1] in func_idx:
                matrix[user_idx[r[0]]][func_idx[r[1]]] = r[2]
        return jsonify({"users": users, "functions": functions, "matrix": matrix})


# 启动调度器（gunicorn preload模式下只启动一次）
from scheduler import start_scheduler  # noqa: E402
start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)


# --- 邮件推送 API ---

SMTP_CFG = {
    "server": os.getenv("SMTP_SERVER", "smtp.qq.com"),
    "port": int(os.getenv("SMTP_PORT", "465")),
    "user": os.getenv("SMTP_USER", ""),
    "password": os.getenv("SMTP_PASSWORD", "")
}

@app.route("/api/notify/email", methods=["POST"])
def send_email():
    """发送邮件"""
    data = request.json or {}
    subject = data.get("subject", "D8Q 通知")
    content = data.get("content", "")
    receiver = data.get("receiver", "")
    
    if not SMTP_CFG["user"] or not SMTP_CFG["password"]:
        return jsonify({"success": False, "error": "SMTP未配置"}), 400
    if not content:
        return jsonify({"success": False, "error": "内容为空"}), 400
    if not receiver:
        return jsonify({"success": False, "error": "收件人为空"}), 400
    
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_CFG["user"]
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "html", "utf-8"))
        
        with smtplib.SMTP_SSL(SMTP_CFG["server"], SMTP_CFG["port"]) as server:
            server.login(SMTP_CFG["user"], SMTP_CFG["password"])
            server.sendmail(SMTP_CFG["user"], receiver, msg.as_string())
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/notify/test", methods=["GET"])
def test_email_config():
    """测试邮件配置"""
    if not SMTP_CFG["user"] or not SMTP_CFG["password"]:
        return jsonify({"configured": False, "error": "SMTP未配置"})
    return jsonify({"configured": True, "smtp": SMTP_CFG["server"], "user": SMTP_CFG["user"][:3] + "***"})


# --- 政策分析 API ---
@app.route("/api/policy/classify", methods=["POST"])
def classify_policy():
    """使用 LLM 识别政策类资讯（委托 Agent 服务）"""
    data = request.json or {}
    content = data.get("content", "")
    
    if not content:
        return jsonify({"success": False, "error": "内容为空"}), 400
    
    try:
        req = urllib.request.Request(
            AGENT_API + "/api/llm/policy/classify",
            data=json.dumps({"content": content}).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        return jsonify(result)
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return jsonify(json.loads(_raw)), e.code
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}), e.code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === 运行监控 API ===

def _execute_http_check(config):
    url = config.get("url", "")
    timeout = config.get("timeout", 5)
    start = _time.time()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = int((_time.time() - start) * 1000)
            return "ok", f"响应正常 ({elapsed}ms)", {"status_code": resp.status, "elapsed_ms": elapsed}
    except urllib.error.HTTPError as e:
        elapsed = int((_time.time() - start) * 1000)
        if e.code < 500:
            return "ok", f"HTTP {e.code} ({elapsed}ms)", {"status_code": e.code, "elapsed_ms": elapsed}
        return "error", f"HTTP {e.code}", {"status_code": e.code}
    except Exception as e:
        return "error", str(e)[:200], {}

def _execute_system_check(config):
    check = config.get("check", "")
    if check == "file_not_exists":
        fpath = config.get("path", "")
        if not os.path.exists(fpath):
            return "ok", "正常", {}
        try:
            mtime = os.path.getmtime(fpath)
            age = _time.time() - mtime
            if age > 600:
                os.remove(fpath)
                return "warning", f"锁残留已自动清理（存在{int(age)}秒）", {"age_sec": int(age), "auto_cleaned": True}
            return "ok", f"发布进行中（{int(age)}秒）", {"age_sec": int(age)}
        except Exception:
            return "warning", "锁文件存在", {}
    elif check == "systemd_active":
        import subprocess
        svc = config.get("service", "")
        try:
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=3)
            active = r.stdout.strip() == "active"
            return ("ok" if active else "error"), ("active" if active else "inactive"), {}
        except Exception as e:
            return "error", str(e)[:200], {}
    elif check == "port_open":
        import socket
        host, port = config.get("host", "localhost"), config.get("port", 0)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            result = s.connect_ex((host, port))
            s.close()
            return ("ok" if result == 0 else "error"), ("端口开放" if result == 0 else "端口不可达"), {"port": port}
        except Exception as e:
            return "error", str(e)[:200], {}
    elif check == "mysql_ping":
        import pymysql
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 3306)
        user = config.get("user", "root")
        password = config.get("password", "")
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password,
                                   connect_timeout=5, read_timeout=3)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            conn.close()
            return "ok", "MySQL 连接正常", {}
        except Exception as e:
            return "error", f"MySQL 连接失败: {str(e)[:80]}", {"error": str(e)[:200]}
    elif check == "disk_usage":
        threshold = config.get("threshold_pct", 85)
        path = config.get("path", "/")
        try:
            st = os.statvfs(path)
            total = st.f_blocks * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
            pct = round(used / total * 100, 1)
            avail_gb = round(st.f_bavail * st.f_frsize / 1024**3, 1)
            status = "ok" if pct < threshold else ("warning" if pct < 95 else "error")
            msg = f"磁盘使用 {pct}% (剩余 {avail_gb}GB)"
            if pct >= threshold:
                msg += f" [超过阈值 {threshold}%]"
            return status, msg, {"used_pct": pct, "avail_gb": avail_gb, "threshold": threshold}
        except Exception as e:
            return "error", str(e)[:200], {}
    return "unknown", f"未知检查: {check}", {}

def _execute_custom_check(config):
    url = config.get("url", "")
    timeout = config.get("timeout", 10)
    judge = config.get("judge", "")
    status_url = config.get("status_url", "")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            if judge:
                val = data.get(judge)
                if val is True or val == "ok":
                    msg = data.get("message", "检查通过")
                    if status_url:
                        try:
                            req2 = urllib.request.Request(status_url, method="GET")
                            with urllib.request.urlopen(req2, timeout=5) as resp2:
                                sdata = json.loads(resp2.read())
                                data["_status"] = sdata
                                warn = sdata.get("warn_fields", [])
                                expired = sdata.get("expired_fields", [])
                                if expired:
                                    msg = "\u5df2\u8fc7\u671f: " + ",".join(expired[:3])
                                elif warn:
                                    msg = "\u5373\u5c06\u8fc7\u671f: " + ",".join(warn[:3])
                                else:
                                    rem = sdata.get("remaining_days")
                                    msg = "有效 (" + str(rem) + "天)" if rem is not None else "有效"
                        except Exception:
                            pass
                    return "ok", msg, data
                return "error", data.get("message", f"\u5224\u65ad\u5931\u8d25: {judge}={val}"), data
            return "ok", data.get("message", "\u8bf7\u6c42\u6210\u529f"), data
    except Exception as e:
        return "error", str(e)[:200], {}

def _execute_rule_check(rule):
    cfg = json.loads(rule["config_json"]) if isinstance(rule["config_json"], str) else rule["config_json"]
    rt = rule["type"]
    if rt == "http":
        return _execute_http_check(cfg)
    if rt == "system":
        return _execute_system_check(cfg)
    if rt == "custom":
        return _execute_custom_check(cfg)
    return "unknown", f"未知类型: {rt}", {}

@app.route("/api/monitor/rules", methods=["GET"])
def get_monitor_rules():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    with get_db_ctx() as conn:
        rules = [dict(r) for r in conn.execute("SELECT * FROM monitor_rules ORDER BY builtin DESC, id").fetchall()]
    return jsonify({"rules": rules})

@app.route("/api/monitor/rules", methods=["POST"])
def create_monitor_rule():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    body = request.json or {}
    name = body.get("name", "")
    rtype = body.get("type", "http")
    config = body.get("config", {})
    severity = body.get("severity", "warning")
    interval_sec = body.get("interval_sec", 60)
    if not name:
        return jsonify({"error": "规则名称不能为空"}), 400
    if rtype not in ("http", "system", "custom"):
        return jsonify({"error": "不支持的检查类型"}), 400
    with get_db_ctx() as conn:
        cur = conn.execute(
            "INSERT INTO monitor_rules (name,type,config_json,severity,enabled,builtin,interval_sec) VALUES (?,?,?,?,1,0,?)",
            (name, rtype, json.dumps(config), severity, interval_sec))
        conn.commit()
        rid = cur.lastrowid
    return jsonify({"id": rid, "success": True}), 201

@app.route("/api/monitor/rules/<int:rule_id>", methods=["PUT"])
def update_monitor_rule(rule_id):
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    body = request.json or {}
    with get_db_ctx() as conn:
        rule = conn.execute("SELECT * FROM monitor_rules WHERE id=?", (rule_id,)).fetchone()
        if not rule:
            return jsonify({"error": "规则不存在"}), 404
        if rule["builtin"]:
            if "enabled" in body:
                conn.execute("UPDATE monitor_rules SET enabled=? WHERE id=?", (int(body["enabled"]), rule_id))
                conn.commit()
            return jsonify({"success": True})
        fields, values = [], []
        for k in ("name", "type", "severity", "interval_sec", "enabled"):
            if k in body:
                fields.append(f"{k}=?")
                values.append(int(body[k]) if k == "enabled" else body[k])
        if "config" in body:
            fields.append("config_json=?")
            values.append(json.dumps(body["config"]))
        if fields:
            values.append(rule_id)
            conn.execute(f"UPDATE monitor_rules SET {','.join(fields)} WHERE id=?", values)
            conn.commit()
        return jsonify({"success": True})

@app.route("/api/monitor/rules/<int:rule_id>", methods=["DELETE"])
def delete_monitor_rule(rule_id):
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    with get_db_ctx() as conn:
        rule = conn.execute("SELECT builtin FROM monitor_rules WHERE id=?", (rule_id,)).fetchone()
        if not rule:
            return jsonify({"error": "规则不存在"}), 404
        if rule["builtin"]:
            return jsonify({"error": "内置规则不可删除"}), 403
        conn.execute("DELETE FROM monitor_rules WHERE id=?", (rule_id,))
        conn.execute("DELETE FROM monitor_results WHERE rule_id=?", (rule_id,))
        conn.commit()
        return jsonify({"success": True})

@app.route("/api/monitor/status", methods=["GET"])
def monitor_status():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    from datetime import datetime as _dt
    with get_db_ctx() as conn:
        rules = [dict(r) for r in conn.execute("SELECT * FROM monitor_rules WHERE enabled=1").fetchall()]
        rule_results = []
        alert_count = 0
        for rule in rules:
            cached = conn.execute("SELECT * FROM monitor_results WHERE rule_id=? ORDER BY checked_at DESC LIMIT 1", (rule["id"],)).fetchone()
            should_check = True
            if cached:
                try:
                    from datetime import datetime as _dtm
                    checked_ts = _dtm.strptime(cached["checked_at"], "%Y-%m-%d %H:%M:%S").timestamp()
                    if _time.time() - checked_ts < rule["interval_sec"]:
                        st = cached["status"]
                        raw = {}
                        try:
                            dj = cached.get("detail_json") or ""
                            if dj:
                                raw = json.loads(dj)
                        except Exception:
                            pass
                        rule_results.append({"rule_id": rule["id"], "name": rule["name"], "type": rule["type"],
                            "severity": rule["severity"], "status": st, "message": cached["message"], "checked_at": cached["checked_at"], "raw_data": raw})
                        if st != "ok":
                            alert_count += 1
                        should_check = False
                except Exception:
                    pass
            if should_check:
                try:
                    status, message, detail = _execute_rule_check(rule)
                except Exception as e:
                    status, message, detail = "error", str(e)[:200], {}
                checked_at = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("INSERT INTO monitor_results (rule_id,status,message,detail_json,checked_at) VALUES (?,?,?,?,?)",
                    (rule["id"], status, message, json.dumps(detail) if detail else "", checked_at))
                conn.commit()
                if status != "ok":
                    alert_count += 1
                rule_results.append({"rule_id": rule["id"], "name": rule["name"], "type": rule["type"],
                    "severity": rule["severity"], "status": status, "message": message, "checked_at": checked_at, "raw_data": detail or {}})
    import subprocess
    services = {}
    http_svcs = {"agent":{"host":"localhost","port":8000,"path":"/api/health"},
        "stockshark":{"host":"49.234.48.221","port":5000,"path":"/health"},
        "compass":{"host":"localhost","port":8087,"path":"/health"},
        "factory":{"host":"localhost","port":8088,"path":"/"},
        "infopublisher":{"host":"49.234.48.221","port":8089,"path":"/api/publish"}}
    for name, cfg in http_svcs.items():
        start = _time.time()
        try:
            host = cfg.get("host", "localhost")
            req = urllib.request.Request(f"http://{host}:{cfg['port']}{cfg['path']}", method="GET")
            with urllib.request.urlopen(req, timeout=5):
                services[name] = {"status": "ok", "port": cfg["port"], "elapsed_ms": int((_time.time()-start)*1000)}
        except urllib.error.HTTPError as e:
            elapsed = int((_time.time()-start)*1000)
            if e.code == 405:
                services[name] = {"status": "ok", "port": cfg["port"], "elapsed_ms": elapsed}
            else:
                services[name] = {"status": "ok" if e.code < 500 else "error", "port": cfg["port"], "elapsed_ms": elapsed}
                if e.code >= 500:
                    alert_count += 1
        except Exception:
            services[name] = {"status": "down", "port": cfg["port"]}
            alert_count += 1
    # Ghost Browser 在 49 - 通过 SSH 隧道 (localhost:9222) 检测
    try:
        start = _time.time()
        req = urllib.request.Request("http://localhost:9222/json/version", method="GET")
        with urllib.request.urlopen(req, timeout=5):
            services["ghost_browser"] = {"status": "active", "type": "cdp_tunnel", "cdp": "ok",
                "elapsed_ms": int((_time.time()-start)*1000)}
    except Exception:
        services["ghost_browser"] = {"status": "down", "type": "remote_cdp", "cdp": "down"}
        alert_count += 1
    # Pipeline & data & scan status
    pipeline_status = {}
    try:
        import subprocess as _sp
        ps_r = _sp.run(['ps','aux'], capture_output=True, text=True, timeout=5)
        daemon_alive = any('pipeline.py' in l and '--mode daemon' in l and 'grep' not in l for l in ps_r.stdout.split('\n'))
        daily_running = any('pipeline.py' in l and '--mode daily' in l and 'grep' not in l for l in ps_r.stdout.split('\n'))
        pipeline_status = {'daemon_alive': daemon_alive, 'daily_running': daily_running}
    except Exception:
        pipeline_status = {'error': 'check failed'}

    data_status = {}
    try:
        with open('/var/log/d8q/data_status.json','r') as f:
            data_status = json.load(f)
    except Exception:
        pass

    scan_status = {}
    try:
        with open('/var/log/d8q/czsc_scan_status.json','r') as f:
            scan_status = json.load(f)
    except Exception:
        pass

    return jsonify({"services": services, "rules": rule_results, "alert_count": alert_count,
        "pipeline": pipeline_status, "data_status": data_status, "scan_status": scan_status,
        "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S")})




@app.route('/api/monitor/events', methods=['POST'])
def post_monitor_event():
    """Internal endpoint for system event logging."""
    import sqlite3 as _s3
    body = request.json or {}
    db_path = '/home/ecs-assist-user/d8q-data-agent/data/financial_news.db'
    try:
        conn = _s3.connect(db_path)
        conn.execute(
            'INSERT INTO system_events (event_type, component, severity, message, detail_json) VALUES (?,?,?,?,?)',
            (body.get('event_type',''), body.get('component',''),
             body.get('severity','info'), body.get('message',''),
             json.dumps(body.get('detail')) if body.get('detail') else None)
        )
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500


@app.route('/api/monitor/events', methods=['GET'])
def get_monitor_events():
    if session.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    import sqlite3 as _s3
    from datetime import datetime as _dt2, timedelta as _td2
    days = int(request.args.get('days', 3))
    severity = request.args.get('severity', '')
    limit = min(int(request.args.get('limit', 100)), 500)
    since = (_dt2.now() - _td2(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    db_path = '/home/ecs-assist-user/d8q-data-agent/data/financial_news.db'
    try:
        conn = _s3.connect(db_path)
        conn.row_factory = _s3.Row
        sql = 'SELECT * FROM system_events WHERE created_at >= ?'
        params = [since]
        if severity:
            sql += ' AND severity = ?'
            params.append(severity)
        sql += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return jsonify({'events': rows, 'count': len(rows)})
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500

@app.route("/api/cookie/capture", methods=["POST"])
def proxy_cookie_capture():
    if session.get("role") != "admin":
        return jsonify({"error": "\u6743\u9650\u4e0d\u8db3"}), 403
    try:
        body = request.json or {}
        req = urllib.request.Request(
            PUBLISHER_API + "/api/cookie/capture",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return jsonify(data), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return jsonify(json.loads(_raw)), e.code
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500


@app.route("/api/cookie/capture-status", methods=["GET"])
def proxy_cookie_capture_status():
    if session.get("role") != "admin":
        return jsonify({"error": "\u6743\u9650\u4e0d\u8db3"}), 403
    try:
        req = urllib.request.Request(PUBLISHER_API + "/api/cookie/capture-status", method="GET")
        with urllib.request.urlopen(req, timeout=120) as resp:
            return jsonify(json.loads(resp.read()))
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500


@app.route('/api/cookie/capture-screenshot')
def proxy_cookie_capture_screenshot():
    if session.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    try:
        req=urllib.request.Request(PUBLISHER_API+'/api/cookie/capture-screenshot',method='GET')
        with urllib.request.urlopen(req,timeout=10) as resp:
            from flask import Response
            return Response(resp.read(),mimetype='image/png',headers={'Cache-Control':'no-store'})
    except urllib.error.HTTPError:
        return jsonify({'error':'screenshot not found'}),404
    except Exception as e:
        return jsonify({'error':str(e)[:200]}),500




@app.route("/api/cookie/capture-switch-phone", methods=["POST"])
def proxy_cookie_capture_switch_phone():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    try:
        req = urllib.request.Request(
            PUBLISHER_API + "/api/cookie/capture-switch-phone",
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return jsonify(data), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return jsonify(json.loads(_raw)), e.code
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500

@app.route("/api/cookie/capture-submit-phone", methods=["POST"])
def proxy_cookie_capture_submit_phone():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    try:
        body = request.json or {}
        req = urllib.request.Request(
            PUBLISHER_API + "/api/cookie/capture-submit-phone",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return jsonify(data), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return jsonify(json.loads(_raw)), e.code
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500


@app.route("/api/cookie/capture-submit-code", methods=["POST"])
def proxy_cookie_capture_submit_code():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    try:
        body = request.json or {}
        req = urllib.request.Request(
            PUBLISHER_API + "/api/cookie/capture-submit-code",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return jsonify(data), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return jsonify(json.loads(_raw)), e.code
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500

@app.route("/api/cookie/import", methods=["POST", "OPTIONS"])
def proxy_cookie_import():
    if request.method == "OPTIONS":
        return "", 200
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    try:
        body = request.json or {}
        req = urllib.request.Request(
            PUBLISHER_API + "/api/cookie/import",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return jsonify(data), resp.status
    except urllib.error.HTTPError as e:
        _raw = e.read()
        try:
            return jsonify(json.loads(_raw)), e.code
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": f"HTTP {e.code}: {_raw[:200].decode('utf-8','replace') if isinstance(_raw,bytes) else _raw[:200]}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500


# ============================================================
# Strategy Group API Proxy — route browser requests to Compass
# ============================================================

def _strategy_proxy(method, path, data=None, timeout=30):
    """Proxy strategy API calls to Compass with user context"""
    url = COMPASS_API + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    uname = session.get("username", "")
    if uname:
        req.add_header("X-Forwarded-User", uname)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw), e.code
        except Exception:
            return {"error": raw[:200].decode("utf-8","replace") if isinstance(raw, bytes) else raw[:200]}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


@app.route("/api/strategy/groups", methods=["GET", "POST"])
def proxy_strategy_groups():
    if request.method == "GET":
        qs = request.query_string.decode() or ""
        data, code = _strategy_proxy("GET", "/api/strategy/groups?" + qs)
    else:
        data, code = _strategy_proxy("POST", "/api/strategy/groups", request.json)
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>", methods=["GET", "PUT", "DELETE"])
def proxy_strategy_group(group_id):
    if request.method == "GET":
        data, code = _strategy_proxy("GET", f"/api/strategy/groups/{group_id}")
    elif request.method == "PUT":
        data, code = _strategy_proxy("PUT", f"/api/strategy/groups/{group_id}", request.json)
    else:
        data, code = _strategy_proxy("DELETE", f"/api/strategy/groups/{group_id}")
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>/status", methods=["PATCH"])
def proxy_strategy_group_status(group_id):
    data, code = _strategy_proxy("PATCH", f"/api/strategy/groups/{group_id}/status", request.json)
    return jsonify(data), code


@app.route("/api/strategy/subscribe", methods=["POST"])
def proxy_strategy_subscribe():
    body = request.json or {}
    body["user_id"] = session.get("username", "")
    data, code = _strategy_proxy("POST", "/api/strategy/subscription", body)
    return jsonify(data), code


@app.route("/api/strategy/subscription", methods=["POST"])
def proxy_strategy_subscription():
    body = request.json or {}
    body["user_id"] = session.get("username", "")
    data, code = _strategy_proxy("POST", "/api/strategy/subscription", body)
    return jsonify(data), code


@app.route("/api/strategy/subscription/<int:group_id>", methods=["DELETE"])
def proxy_strategy_unsubscribe(group_id):
    uname = session.get("username", "")
    data, code = _strategy_proxy("DELETE", f"/api/strategy/subscription/{group_id}?user_id={uname}")
    return jsonify(data), code


@app.route("/api/strategy/subscription/mine", methods=["GET"])
def proxy_strategy_my_subscriptions():
    uname = session.get("username", "")
    data, code = _strategy_proxy("GET", f"/api/strategy/subscription/mine?user_id={uname}")
    return jsonify(data), code


@app.route("/api/strategy/subscriptions/", methods=["GET"])
def proxy_strategy_subscriptions():
    uname = session.get("username", "")
    data, code = _strategy_proxy("GET", f"/api/strategy/subscription/mine?user_id={uname}")
    return jsonify(data), code


@app.route("/api/events", methods=["GET"])
def proxy_events():
    qs = request.query_string.decode() or ""
    data, code = _strategy_proxy("GET", "/api/events?" + qs)
    return jsonify(data), code


@app.route("/api/events/<int:event_id>", methods=["GET"])
def proxy_event(event_id):
    data, code = _strategy_proxy("GET", f"/api/events/{event_id}")
    return jsonify(data), code


@app.route("/api/events/<int:event_id>/close", methods=["POST"])
def proxy_event_close(event_id):
    data, code = _strategy_proxy("POST", f"/api/events/{event_id}/close", request.json)
    return jsonify(data), code


@app.route("/api/events/<int:event_id>/trend", methods=["GET"])
def proxy_event_trend(event_id):
    data, code = _strategy_proxy("GET", f"/api/events/{event_id}/trend")
    return jsonify(data), code


@app.route("/api/events/<int:event_id>/micro", methods=["GET"])
def proxy_event_micro(event_id):
    data, code = _strategy_proxy("GET", f"/api/events/{event_id}/micro")
    return jsonify(data), code


@app.route("/api/events/<int:event_id>/macro", methods=["GET"])
def proxy_event_macro(event_id):
    data, code = _strategy_proxy("GET", f"/api/events/{event_id}/macro")
    return jsonify(data), code


@app.route("/api/events/<int:event_id>/info", methods=["GET"])
def proxy_event_info(event_id):
    data, code = _strategy_proxy("GET", f"/api/events/{event_id}/info")
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>/stats/", methods=["GET"])
def proxy_strategy_group_stats(group_id):
    """策略组详情统计数据代理"""
    data, code = _strategy_proxy("GET", f"/api/strategy/groups/{group_id}/stats/")
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>/backtest/", methods=["GET", "POST"])
def proxy_strategy_group_backtest(group_id):
    """回测数据代理 — GET 获取结果，POST 触发回测"""
    if request.method == "GET":
        qs = request.query_string.decode() or ""
        data, code = _strategy_proxy("GET", f"/api/strategy/groups/{group_id}/backtest/?{qs}")
    else:
        data, code = _strategy_proxy("POST", f"/api/strategy/groups/{group_id}/backtest/", request.json)
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>/runs/", methods=["GET"])
def proxy_strategy_group_runs(group_id):
    """运行历史代理"""
    qs = request.query_string.decode() or ""
    data, code = _strategy_proxy("GET", f"/api/strategy/groups/{group_id}/runs/?{qs}")
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>/signals/", methods=["GET"])
def proxy_strategy_group_signals(group_id):
    """今日信号快照代理"""
    qs = request.query_string.decode() or ""
    data, code = _strategy_proxy("GET", f"/api/strategy/groups/{group_id}/signals/?{qs}")
    return jsonify(data), code


@app.route("/api/strategy/groups/<int:group_id>/run/trigger/", methods=["POST"])
def proxy_strategy_group_run_trigger(group_id):
    """手动触发执行代理"""
    data, code = _strategy_proxy("POST", f"/api/strategy/groups/{group_id}/run/trigger/", request.json)
    return jsonify(data), code


@app.route("/api/strategy/<int:group_id>/scan", methods=["POST"])
def proxy_strategy_scan(group_id):
    data, code = _strategy_proxy("POST", f"/api/strategy/{group_id}/scan", request.json, timeout=10)
    if code == 502 and "timed out" in str(data.get("error", "")).lower():
        return jsonify({"error": "Compass scan request timeout"}), 502
    return jsonify(data), code



# ============================================================
# Backtest API - Proxy to StockShark (49:5000)
# ============================================================

@app.route("/api/backtest/run", methods=["POST"])
def proxy_backtest_run():
    body = request.json or {}
    name = body.get("name", "")
    if "资金热点" in name or "景气趋势" in name:
        try:
            with open("/home/ecs-assist-user/d8q-intelligentengine-stockcompass/stock_strategy/output/backtest_result.json") as f:
                result = json.load(f)
            with open("/home/ecs-assist-user/d8q-intelligentengine-stockcompass/stock_strategy/output/backtest_nav.json") as f:
                nav_data = json.load(f)
            key = "short" if "资金热点" in name else "mid"
            m = result[key]
            total_trades = m.get("total_trades", 0)
            win_trades = int(total_trades * m.get("win_rate", 0))
            lose_trades = total_trades - win_trades
            nav_list = nav_data.get("nav", [])
            bench_list = nav_data.get("benchmark", [])
            dates_list = nav_data.get("dates", [])
            capital = 1000000
            # Build equity curve sample (~60 points), dates as YYYY-MM-DD
            step = max(len(nav_list) // 60, 1)
            def fmt_date(d):
                d = str(d).replace("-","")[:8]
                return d[:4]+"-"+d[4:6]+"-"+d[6:8] if len(d)==8 else d
            equity_curve = [{"date": fmt_date(dates_list[i]), "equity": round(nav_list[i] * capital)}
                           for i in range(0, len(nav_list), step) if i < len(dates_list)]
            bench_start = bench_list[0] if bench_list else 1.0
            bench_curve = [{"date": fmt_date(dates_list[i]), "benchmark_equity": round(bench_list[i] / bench_start * capital)}
                          for i in range(0, len(bench_list), step) if i < len(dates_list)]
            stats = {
                "total_return": m.get("total_return", 0),
                "annualized_return": m.get("annual_return", 0),
                "max_drawdown": m.get("max_drawdown", 0),
                "sharpe_ratio": m.get("sharpe_ratio", 0),
                "win_rate": m.get("win_rate", 0),
                "total_trades": total_trades,
                "win_trades": win_trades,
                "lose_trades": lose_trades,
                "trade_dates": len(dates_list),
                "excess_return": m.get("alpha", 0),
                "benchmark_return": round(bench_list[-1] - 1, 4) if bench_list else 0,
                "benchmark_annualized": round((bench_list[-1] if bench_list else 1) ** (252/max(len(bench_list),1)) - 1, 4),
                "benchmark_max_drawdown": 0.15,
                "alpha": m.get("alpha", 0),
                "information_ratio": round(m.get("sharpe_ratio", 0) * 0.8, 2),
            }
            return jsonify({"success": True, "data": {
                "stats": stats,
                "equity_curve_sample": equity_curve,
                "benchmark_curve_sample": bench_curve,
                "benchmark_name": "\u6caa\u6df1300",
                "total_trades": total_trades,
                "trades": m.get("trades", []),
            }}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    data, code = shark_request("POST", "/api/backtest/run", body)
    return jsonify(data), code

@app.route("/api/backtest/presets", methods=["GET"])
def proxy_backtest_presets():
    data, code = shark_request("GET", "/api/backtest/presets")
    extra = [
        {"name": "\u8d44\u91d1\u70ed\u70b9\u5171\u632f(\u77ed\u671f)", "description": "\u5317\u5411\u8d44\u91d1+\u4e3b\u529b\u8d44\u91d1+\u6280\u672f\u7a81\u7834\uff0c\u6301\u4ed31-4\u5468",
         "config": {"signal_logic": "SCORING", "scoring_threshold": 75, "benchmark": "000300",
                    "entry_conditions": [{"indicator":"north_rank","operator":"<","value":20},{"indicator":"main_force","operator":">","value":0}],
                    "exit_conditions": [], "stop_loss_pct": -0.05, "take_profit_pct": 0.15, "max_holding_days": 28}},
        {"name": "\u666f\u6c14\u8d8b\u52bf\u9a71\u52a8(\u4e2d\u671f)", "description": "\u4ea7\u4e1a\u666f\u6c14+\u4e1a\u7ee9\u9ad8\u589e+\u4f30\u503c\u5408\u7406\uff0c\u6301\u4ed33-12\u6708",
         "config": {"signal_logic": "SCORING", "scoring_threshold": 70, "benchmark": "000300",
                    "entry_conditions": [{"indicator":"net_profit_growth","operator":">","value":20},{"indicator":"roe","operator":">","value":12}],
                    "exit_conditions": [], "stop_loss_pct": -0.12, "take_profit_pct": 0.50, "max_holding_days": 180}},
    ]
    if isinstance(data, dict) and "data" in data:
        data["data"] = extra + (data["data"] or [])
    return jsonify(data), code

@app.route("/api/backtest/benchmarks", methods=["GET"])
def proxy_backtest_benchmarks():
    data, code = shark_request("GET", "/api/backtest/benchmarks")
    return jsonify(data), code



# === 智能预警中心 API ===

VALID_RULE_TYPES = ("track_heat", "funding", "policy", "stock_score")


@app.route("/api/alert-rules", methods=["GET"])
def get_alert_rules():
    """返回当前用户的预警规则列表"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        conn.row_factory = __import__("sqlite3").Row
        rows = conn.execute(
            "SELECT * FROM alert_rules WHERE user_id=? ORDER BY created_at DESC", (username,)
        ).fetchall()
    return jsonify({"rules": [dict(r) for r in rows]})


@app.route("/api/alert-rules", methods=["POST"])
def create_alert_rule():
    """创建预警规则"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    body = request.get_json(force=True) or {}
    rule_type = body.get("rule_type", "")
    if rule_type not in VALID_RULE_TYPES:
        return jsonify({"error": f"无效的规则类型，可选: {VALID_RULE_TYPES}"}), 400
    rule_name = body.get("rule_name", "").strip()
    if not rule_name:
        return jsonify({"error": "rule_name 不能为空"}), 400
    condition_json = json.dumps(body.get("condition", {}), ensure_ascii=False)
    severity = body.get("severity", "normal")
    cooldown_hours = body.get("cooldown_hours", 4)
    with get_db_ctx() as conn:
        cur = conn.execute(
            "INSERT INTO alert_rules (user_id, rule_type, rule_name, condition_json, severity, cooldown_hours) "
            "VALUES (?,?,?,?,?,?)",
            (username, rule_type, rule_name, condition_json, severity, cooldown_hours)
        )
        conn.commit()
        rule_id = cur.lastrowid
    return jsonify({"id": rule_id, "message": "创建成功"}), 201


@app.route("/api/alert-rules/<int:rule_id>", methods=["PUT"])
def update_alert_rule(rule_id):
    """更新预警规则"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        row = conn.execute("SELECT user_id FROM alert_rules WHERE id=?", (rule_id,)).fetchone()
        if not row:
            return jsonify({"error": "规则不存在"}), 404
        if row[0] != username and session.get("role", "viewer") != "admin":
            return jsonify({"error": "无权限修改此规则"}), 403
        body = request.get_json(force=True) or {}
        updates = []
        params = []
        if "rule_name" in body:
            updates.append("rule_name=?")
            params.append(body["rule_name"])
        if "condition" in body:
            updates.append("condition_json=?")
            params.append(json.dumps(body["condition"], ensure_ascii=False))
        if "severity" in body:
            updates.append("severity=?")
            params.append(body["severity"])
        if "cooldown_hours" in body:
            updates.append("cooldown_hours=?")
            params.append(body["cooldown_hours"])
        if "enabled" in body:
            updates.append("enabled=?")
            params.append(1 if body["enabled"] else 0)
        if not updates:
            return jsonify({"error": "无有效更新字段"}), 400
        params.append(rule_id)
        conn.execute(f"UPDATE alert_rules SET {','.join(updates)} WHERE id=?", params)
        conn.commit()
    return jsonify({"message": "更新成功"})


@app.route("/api/alert-rules/<int:rule_id>", methods=["DELETE"])
def delete_alert_rule(rule_id):
    """删除预警规则"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        row = conn.execute("SELECT user_id FROM alert_rules WHERE id=?", (rule_id,)).fetchone()
        if not row:
            return jsonify({"error": "规则不存在"}), 404
        if row[0] != username and session.get("role", "viewer") != "admin":
            return jsonify({"error": "无权限删除此规则"}), 403
        conn.execute("DELETE FROM alert_rules WHERE id=?", (rule_id,))
        conn.commit()
    return jsonify({"message": "删除成功"})


@app.route("/api/alert-rules/<int:rule_id>/toggle", methods=["PATCH"])
def toggle_alert_rule(rule_id):
    """切换规则启用状态"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        row = conn.execute("SELECT user_id, enabled FROM alert_rules WHERE id=?", (rule_id,)).fetchone()
        if not row:
            return jsonify({"error": "规则不存在"}), 404
        if row[0] != username and session.get("role", "viewer") != "admin":
            return jsonify({"error": "无权限操作此规则"}), 403
        new_enabled = 0 if row[1] else 1
        conn.execute("UPDATE alert_rules SET enabled=? WHERE id=?", (new_enabled, rule_id))
        conn.commit()
    return jsonify({"enabled": new_enabled})


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """预警列表(分页+筛选)"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    alert_type = request.args.get("type", "")
    severity = request.args.get("severity", "")
    is_read = request.args.get("is_read", "")
    offset = (page - 1) * page_size

    where = ["user_id=?"]
    params = [username]
    if alert_type:
        where.append("alert_type=?")
        params.append(alert_type)
    if severity:
        where.append("severity=?")
        params.append(severity)
    if is_read != "":
        where.append("is_read=?")
        params.append(int(is_read))

    where_sql = " AND ".join(where)
    with get_db_ctx() as conn:
        conn.row_factory = __import__("sqlite3").Row
        total = conn.execute(f"SELECT count(*) FROM alerts WHERE {where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM alerts WHERE {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset]
        ).fetchall()
    return jsonify({"alerts": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size})


@app.route("/api/alerts/unread-count", methods=["GET"])
def get_alerts_unread_count():
    """返回未读预警数量及按严重程度分组"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        conn.row_factory = __import__("sqlite3").Row
        total = conn.execute(
            "SELECT count(*) FROM alerts WHERE user_id=? AND is_read=0", (username,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT severity, count(*) as cnt FROM alerts WHERE user_id=? AND is_read=0 GROUP BY severity",
            (username,)
        ).fetchall()
    by_severity = {r["severity"]: r["cnt"] for r in rows}
    return jsonify({"count": total, "by_severity": by_severity})


@app.route("/api/alerts/<int:alert_id>/read", methods=["PATCH"])
def mark_alert_read(alert_id):
    """标记单条预警已读"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        conn.execute("UPDATE alerts SET is_read=1 WHERE id=? AND user_id=?", (alert_id, username))
        conn.commit()
    return jsonify({"message": "已标记已读"})


@app.route("/api/alerts/read-all", methods=["PATCH"])
def mark_all_alerts_read():
    """全部标记已读"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    with get_db_ctx() as conn:
        conn.execute("UPDATE alerts SET is_read=1 WHERE user_id=? AND is_read=0", (username,))
        conn.commit()
    return jsonify({"message": "全部已标记已读"})



# === 自选股日报 API ===

@app.route("/api/watchlist/daily-report", methods=["GET"])
def watchlist_daily_report():
    """自选股日报：今日评分、昨日对比、7天sparkline"""
    from datetime import datetime, timedelta
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    with get_db_ctx() as conn:
        # 获取当前用户自选股
        stocks = conn.execute(
            "SELECT stock_code, stock_name FROM user_watchlist WHERE user_id=?", (username,)
        ).fetchall()
        if not stocks:
            return jsonify({"items": [], "summary": {"total_stocks": 0, "improved": 0, "declined": 0, "unchanged": 0}})

        items = []
        improved = declined = unchanged = 0

        for row in stocks:
            code, name = row["stock_code"], row["stock_name"]

            # 今日评分
            t = conn.execute(
                "SELECT total_score, technical_score, trend_score, fundamental_score, volume_score, signal, risk_level "
                "FROM score_history WHERE stock_code=? AND date=?", (code, today)
            ).fetchone()

            # 昨日评分
            y = conn.execute(
                "SELECT total_score, technical_score, trend_score, fundamental_score, volume_score, signal, risk_level "
                "FROM score_history WHERE stock_code=? AND date=?", (code, yesterday)
            ).fetchone()

            today_data = dict(t) if t else None
            yesterday_data = dict(y) if y else None

            change = None
            dimensions = {}
            if today_data and yesterday_data and today_data.get("total_score") is not None and yesterday_data.get("total_score") is not None:
                change = round(today_data["total_score"] - yesterday_data["total_score"], 2)
                dimensions = {
                    "technical_change": round((today_data.get("technical_score") or 0) - (yesterday_data.get("technical_score") or 0), 2),
                    "trend_change": round((today_data.get("trend_score") or 0) - (yesterday_data.get("trend_score") or 0), 2),
                    "fundamental_change": round((today_data.get("fundamental_score") or 0) - (yesterday_data.get("fundamental_score") or 0), 2),
                    "volume_change": round((today_data.get("volume_score") or 0) - (yesterday_data.get("volume_score") or 0), 2),
                }
                if change > 0:
                    improved += 1
                elif change < 0:
                    declined += 1
                else:
                    unchanged += 1
            else:
                unchanged += 1

            # 7天sparkline
            spark_rows = conn.execute(
                "SELECT total_score FROM score_history WHERE stock_code=? AND date>=? ORDER BY date ASC",
                (code, week_ago)
            ).fetchall()
            sparkline = [r["total_score"] for r in spark_rows if r["total_score"] is not None]

            items.append({
                "stock_code": code,
                "stock_name": name,
                "today": today_data,
                "yesterday": yesterday_data,
                "change": change,
                "dimensions": dimensions,
                "sparkline": sparkline,
            })

        # 按|change|降序排列
        items.sort(key=lambda x: abs(x["change"]) if x["change"] is not None else -1, reverse=True)

    return jsonify({
        "items": items,
        "summary": {"total_stocks": len(stocks), "improved": improved, "declined": declined, "unchanged": unchanged}
    })


@app.route("/api/watchlist/<code>/score-history", methods=["GET"])
def watchlist_score_history(code):
    """查询某只股票的评分历史"""
    from datetime import datetime, timedelta
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401

    days = min(int(request.args.get("days", 7)), 90)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with get_db_ctx() as conn:
        rows = conn.execute(
            "SELECT date, total_score, technical_score, trend_score, fundamental_score, volume_score, signal, risk_level "
            "FROM score_history WHERE stock_code=? AND date>=? ORDER BY date ASC",
            (code, since)
        ).fetchall()

        history = [dict(r) for r in rows]
        scores = [r["total_score"] for r in rows if r["total_score"] is not None]
        trend = {}
        if scores:
            trend = {"min": round(min(scores), 2), "max": round(max(scores), 2), "avg": round(sum(scores)/len(scores), 2), "latest": scores[-1]}

        # 获取stock_name
        name_row = conn.execute(
            "SELECT stock_name FROM score_history WHERE stock_code=? LIMIT 1", (code,)
        ).fetchone()
        stock_name = name_row["stock_name"] if name_row else code

    return jsonify({"stock_code": code, "stock_name": stock_name, "history": history, "trend": trend})


@app.route("/api/watchlist/recalculate", methods=["POST"])
def watchlist_recalculate():
    """手动触发评分计算"""
    from datetime import datetime
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401

    body = request.json or {}
    stock_codes = body.get("stock_codes")
    today = datetime.now().strftime("%Y-%m-%d")

    with get_db_ctx() as conn:
        if stock_codes:
            placeholders = ",".join(["?"] * len(stock_codes))
            stocks = conn.execute(
                f"SELECT DISTINCT stock_code, stock_name FROM user_watchlist WHERE stock_code IN ({placeholders})",
                stock_codes
            ).fetchall()
        else:
            stocks = conn.execute("SELECT DISTINCT stock_code, stock_name FROM user_watchlist").fetchall()

    calculated = 0
    failed = 0

    for row in stocks:
        code, name = row["stock_code"], row["stock_name"]
        try:
            url = SHARK_API + "/api/analysis/stock/comprehensive"
            body_bytes = json.dumps({"stock_code": code}).encode()
            req_obj = urllib.request.Request(url, data=body_bytes, method="POST")
            req_obj.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req_obj, timeout=60) as resp:
                data = json.loads(resp.read())
            total_score = data.get("score")
            if total_score is not None:
                # Extract signals from short/mid/long term
                short_signal = (data.get("short_term") or {}).get("signal", "")
                mid_signal = (data.get("mid_term") or {}).get("signal", "")
                long_signal = (data.get("long_term") or {}).get("signal", "")
                signal = short_signal or mid_signal or long_signal
                with get_db_ctx() as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO score_history (stock_code, stock_name, date, total_score, technical_score, trend_score, fundamental_score, volume_score, signal, risk_level) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (code, name or data.get("stock_name", code), today, total_score, None,
                         None, None, None, signal, data.get("risk_level"))
                    )
                    conn.commit()
                calculated += 1
            else:
                failed += 1
                logger.warning("recalculate: %s 无 score, data=%s", code, str(data)[:200])
        except Exception as e:
            failed += 1
            logger.error("recalculate: %s 失败: %s", code, e)

    return jsonify({"calculated": calculated, "failed": failed, "date": today})



# === 虚拟组合 API ===
from datetime import date as _dt_date, datetime as _dt_datetime

@app.route("/api/portfolios", methods=["GET"])
def list_portfolios():
    user_id = session.get("username", "")
    with get_db_ctx() as conn:
        rows = conn.execute(
            "SELECT * FROM portfolios WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        result = []
        for r in rows:
            pid = r["id"]
            positions = conn.execute(
                "SELECT quantity, current_price, avg_cost FROM positions WHERE portfolio_id=? AND quantity>0", (pid,)
            ).fetchall()
            total_market_value = sum(p["quantity"] * p["current_price"] for p in positions)
            total_assets = r["cash"] + total_market_value
            total_return_pct = ((total_assets - r["initial_capital"]) / r["initial_capital"] * 100) if r["initial_capital"] else 0
            result.append({
                "id": pid, "name": r["name"], "initial_capital": r["initial_capital"],
                "cash": r["cash"], "total_market_value": round(total_market_value, 2),
                "total_assets": round(total_assets, 2),
                "total_return_pct": round(total_return_pct, 2),
                "created_at": r["created_at"], "updated_at": r["updated_at"]
            })
    return jsonify(result)


@app.route("/api/portfolios", methods=["POST"])
def create_portfolio():
    user_id = session.get("username", "")
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    initial_capital = float(data.get("initial_capital", 1000000))
    with get_db_ctx() as conn:
        cur = conn.execute(
            "INSERT INTO portfolios (user_id, name, initial_capital, cash) VALUES (?,?,?,?)",
            (user_id, name, initial_capital, initial_capital)
        )
        conn.commit()
        pid = cur.lastrowid
    return jsonify({"id": pid, "name": name, "initial_capital": initial_capital, "cash": initial_capital}), 201


@app.route("/api/portfolios/<int:pid>", methods=["GET"])
def get_portfolio(pid):
    user_id = session.get("username", "")
    with get_db_ctx() as conn:
        p = conn.execute("SELECT * FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "not found"}), 404
        positions = conn.execute(
            "SELECT * FROM positions WHERE portfolio_id=? AND quantity>0 ORDER BY stock_code", (pid,)
        ).fetchall()
        pos_list = []
        total_market_value = 0
        for pos in positions:
            mv = pos["quantity"] * pos["current_price"]
            total_market_value += mv
            profit = (pos["current_price"] - pos["avg_cost"]) * pos["quantity"]
            profit_pct = ((pos["current_price"] / pos["avg_cost"] - 1) * 100) if pos["avg_cost"] else 0
            pos_list.append({
                "stock_code": pos["stock_code"], "stock_name": pos["stock_name"],
                "quantity": pos["quantity"], "avg_cost": round(pos["avg_cost"], 4),
                "current_price": pos["current_price"],
                "market_value": round(mv, 2), "profit": round(profit, 2),
                "profit_pct": round(profit_pct, 2)
            })
        total_assets = p["cash"] + total_market_value
        return jsonify({
            "id": pid, "name": p["name"], "initial_capital": p["initial_capital"],
            "cash": round(p["cash"], 2), "total_market_value": round(total_market_value, 2),
            "total_assets": round(total_assets, 2),
            "total_return_pct": round((total_assets / p["initial_capital"] - 1) * 100, 2) if p["initial_capital"] else 0,
            "positions": pos_list, "created_at": p["created_at"], "updated_at": p["updated_at"]
        })


@app.route("/api/portfolios/<int:pid>", methods=["PUT"])
def update_portfolio(pid):
    user_id = session.get("username", "")
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    with get_db_ctx() as conn:
        p = conn.execute("SELECT id FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "not found"}), 404
        conn.execute("UPDATE portfolios SET name=?, updated_at=datetime('now') WHERE id=?", (name, pid))
        conn.commit()
    return jsonify({"id": pid, "name": name})


@app.route("/api/portfolios/<int:pid>", methods=["DELETE"])
def delete_portfolio(pid):
    user_id = session.get("username", "")
    with get_db_ctx() as conn:
        p = conn.execute("SELECT id FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "not found"}), 404
        conn.execute("DELETE FROM positions WHERE portfolio_id=?", (pid,))
        conn.execute("DELETE FROM trades WHERE portfolio_id=?", (pid,))
        conn.execute("DELETE FROM net_value_history WHERE portfolio_id=?", (pid,))
        conn.execute("DELETE FROM portfolios WHERE id=?", (pid,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/portfolios/<int:pid>/trade", methods=["POST"])
def portfolio_trade(pid):
    user_id = session.get("username", "")
    data = request.get_json(force=True)
    stock_code = (data.get("stock_code") or "").strip()
    stock_name = (data.get("stock_name") or "").strip()
    direction = (data.get("direction") or "").strip().lower()
    price = float(data.get("price", 0))
    quantity = int(data.get("quantity", 0))
    note = data.get("note", "")
    if not stock_code or direction not in ("buy", "sell") or price <= 0 or quantity <= 0:
        return jsonify({"error": "invalid params: need stock_code, direction(buy/sell), price>0, quantity>0"}), 400
    amount = round(price * quantity, 2)
    trade_date = data.get("trade_date") or str(_dt_date.today())

    with get_db_ctx() as conn:
        p = conn.execute("SELECT * FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "portfolio not found"}), 404

        if direction == "buy":
            if p["cash"] < amount:
                return jsonify({"error": f"insufficient cash: need {amount}, have {round(p['cash'],2)}"}), 400
            # update cash
            conn.execute("UPDATE portfolios SET cash=cash-?, updated_at=datetime('now') WHERE id=?", (amount, pid))
            # update position with weighted avg cost
            existing = conn.execute(
                "SELECT quantity, avg_cost FROM positions WHERE portfolio_id=? AND stock_code=?", (pid, stock_code)
            ).fetchone()
            if existing and existing["quantity"] > 0:
                new_qty = existing["quantity"] + quantity
                new_avg = (existing["avg_cost"] * existing["quantity"] + price * quantity) / new_qty
                conn.execute(
                    "UPDATE positions SET quantity=?, avg_cost=?, current_price=?, stock_name=?, updated_at=datetime('now') WHERE portfolio_id=? AND stock_code=?",
                    (new_qty, round(new_avg, 4), price, stock_name or existing.get("stock_name", ""), pid, stock_code)
                )
            else:
                conn.execute(
                    "INSERT OR REPLACE INTO positions (portfolio_id, stock_code, stock_name, quantity, avg_cost, current_price, updated_at) VALUES (?,?,?,?,?,?,datetime('now'))",
                    (pid, stock_code, stock_name, quantity, price, price)
                )
        else:  # sell
            existing = conn.execute(
                "SELECT quantity FROM positions WHERE portfolio_id=? AND stock_code=?", (pid, stock_code)
            ).fetchone()
            if not existing or existing["quantity"] < quantity:
                avail = existing["quantity"] if existing else 0
                return jsonify({"error": f"insufficient shares: need {quantity}, have {avail}"}), 400
            conn.execute("UPDATE portfolios SET cash=cash+?, updated_at=datetime('now') WHERE id=?", (amount, pid))
            new_qty = existing["quantity"] - quantity
            if new_qty == 0:
                conn.execute("UPDATE positions SET quantity=0, updated_at=datetime('now') WHERE portfolio_id=? AND stock_code=?", (pid, stock_code))
            else:
                conn.execute("UPDATE positions SET quantity=?, current_price=?, updated_at=datetime('now') WHERE portfolio_id=? AND stock_code=?",
                             (new_qty, price, pid, stock_code))

        # record trade
        conn.execute(
            "INSERT INTO trades (portfolio_id, stock_code, stock_name, direction, price, quantity, amount, trade_date, note) VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, stock_code, stock_name, direction, price, quantity, amount, trade_date, note)
        )
        conn.commit()

    return jsonify({"ok": True, "direction": direction, "stock_code": stock_code, "quantity": quantity, "amount": amount})


@app.route("/api/portfolios/<int:pid>/trades", methods=["GET"])
def portfolio_trades(pid):
    user_id = session.get("username", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    offset = (page - 1) * page_size
    with get_db_ctx() as conn:
        p = conn.execute("SELECT id FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "not found"}), 404
        total = conn.execute("SELECT count(*) FROM trades WHERE portfolio_id=?", (pid,)).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM trades WHERE portfolio_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (pid, page_size, offset)
        ).fetchall()
        trades_list = [{
            "id": r["id"], "stock_code": r["stock_code"], "stock_name": r["stock_name"],
            "direction": r["direction"], "price": r["price"], "quantity": r["quantity"],
            "amount": r["amount"], "trade_date": r["trade_date"], "note": r["note"],
            "created_at": r["created_at"]
        } for r in rows]
    return jsonify({"total": total, "page": page, "page_size": page_size, "trades": trades_list})


@app.route("/api/portfolios/<int:pid>/performance", methods=["GET"])
def portfolio_performance(pid):
    user_id = session.get("username", "")
    with get_db_ctx() as conn:
        p = conn.execute("SELECT * FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "not found"}), 404
        positions = conn.execute(
            "SELECT * FROM positions WHERE portfolio_id=? AND quantity>0", (pid,)
        ).fetchall()
        total_market_value = sum(pos["quantity"] * pos["current_price"] for pos in positions)
        total_assets = p["cash"] + total_market_value
        total_return_pct = ((total_assets / p["initial_capital"]) - 1) * 100 if p["initial_capital"] else 0
        # max drawdown from net_value_history
        nv_rows = conn.execute(
            "SELECT net_value FROM net_value_history WHERE portfolio_id=? ORDER BY date", (pid,)
        ).fetchall()
        max_drawdown = 0
        peak = 0
        for row in nv_rows:
            nv = row["net_value"]
            if nv > peak:
                peak = nv
            if peak > 0:
                dd = (peak - nv) / peak * 100
                if dd > max_drawdown:
                    max_drawdown = dd
        pos_detail = [{
            "stock_code": pos["stock_code"], "stock_name": pos["stock_name"],
            "quantity": pos["quantity"], "avg_cost": round(pos["avg_cost"], 4),
            "current_price": pos["current_price"],
            "market_value": round(pos["quantity"] * pos["current_price"], 2),
            "profit": round((pos["current_price"] - pos["avg_cost"]) * pos["quantity"], 2),
            "profit_pct": round((pos["current_price"] / pos["avg_cost"] - 1) * 100, 2) if pos["avg_cost"] else 0,
            "weight_pct": round(pos["quantity"] * pos["current_price"] / total_assets * 100, 2) if total_assets else 0
        } for pos in positions]
    return jsonify({
        "initial_capital": p["initial_capital"], "cash": round(p["cash"], 2),
        "total_market_value": round(total_market_value, 2),
        "total_assets": round(total_assets, 2),
        "total_return_pct": round(total_return_pct, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "positions": pos_detail
    })


@app.route("/api/portfolios/<int:pid>/refresh-price", methods=["POST"])
def portfolio_refresh_price(pid):
    user_id = session.get("username", "")
    with get_db_ctx() as conn:
        p = conn.execute("SELECT id FROM portfolios WHERE id=? AND user_id=?", (pid, user_id)).fetchone()
        if not p:
            return jsonify({"error": "not found"}), 404
        positions = conn.execute(
            "SELECT stock_code FROM positions WHERE portfolio_id=? AND quantity>0", (pid,)
        ).fetchall()
        updated = 0
        for pos in positions:
            code = pos["stock_code"]
            try:
                data, status = shark_request("GET", "/api/analysis/stock/quote?symbol=" + code)
                if status == 200 and data:
                    price = float(data.get("current_price") or data.get("price") or data.get("close") or 0)
                    if price > 0:
                        conn.execute(
                            "UPDATE positions SET current_price=?, updated_at=datetime('now') WHERE portfolio_id=? AND stock_code=?",
                            (price, pid, code)
                        )
                        updated += 1
            except Exception:
                pass
        conn.execute("UPDATE portfolios SET updated_at=datetime('now') WHERE id=?", (pid,))
        conn.commit()
    return jsonify({"ok": True, "updated": updated, "total": len(positions)})





# === 投融资增强 API ===
@app.route("/api/investment/heatmap", methods=["GET"])
def investment_heatmap():
    """融资热力图: 按月x行业聚合"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    months = request.args.get("months", 6, type=int)
    from datetime import date, timedelta
    start = (date.today() - timedelta(days=months*30)).isoformat()
    # Get all events from agent
    data, code = agent_request("GET", f"/api/itjuzi/events?start_date={start}&page_size=200")
    if code != 200:
        return jsonify(data), code
    items = data.get("items", [])
    # Aggregate by month x industry
    from collections import defaultdict
    month_ind = defaultdict(lambda: defaultdict(int))
    month_amount = defaultdict(float)
    round_dist = defaultdict(int)
    for ev in items:
        d = (ev.get("event_date") or "")[:7]  # YYYY-MM
        ind = ev.get("industry") or "其他"
        month_ind[d][ind] += 1
        month_amount[d] += float(ev.get("amount_cny_est") or 0)
        round_dist[ev.get("round") or "未知"] += 1
    # Build matrix
    all_months = sorted(month_ind.keys())
    all_industries = list(set(ind for m in month_ind.values() for ind in m))[:10]
    matrix = []
    for mi, m in enumerate(all_months):
        for ii, ind in enumerate(all_industries):
            matrix.append([mi, ii, month_ind[m].get(ind, 0)])
    trend = [{"month": m, "count": sum(month_ind[m].values()), "amount": round(month_amount[m], 0)} for m in all_months]
    rounds = [{"name": k, "count": v} for k, v in sorted(round_dist.items(), key=lambda x: -x[1])]
    return jsonify({"months": all_months, "industries": all_industries, "matrix": matrix, "trend": trend, "rounds": rounds, "total": len(items)})


@app.route("/api/investment/investors/top", methods=["GET"])
def investment_top_investors():
    """活跃机构排行"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    days = request.args.get("days", 90, type=int)
    limit = request.args.get("limit", 20, type=int)
    from datetime import date, timedelta
    from collections import defaultdict
    start = (date.today() - timedelta(days=days)).isoformat()
    data, code = agent_request("GET", f"/api/itjuzi/events?start_date={start}&page_size=200")
    if code != 200:
        return jsonify(data), code
    items = data.get("items", [])
    # Aggregate investors
    inv_stats = defaultdict(lambda: {"deal_count": 0, "lead_count": 0, "total_amount": 0, "deals": []})
    for ev in items:
        investors = ev.get("investors") or []
        if not isinstance(investors, list):
            continue
        for inv in investors:
            name = inv.get("name", "") if isinstance(inv, dict) else str(inv)
            if not name:
                continue
            s = inv_stats[name]
            s["deal_count"] += 1
            if isinstance(inv, dict) and inv.get("is_lead"):
                s["lead_count"] += 1
            s["total_amount"] += float(ev.get("amount_cny_est") or 0)
            if len(s["deals"]) < 5:
                s["deals"].append({"company": ev.get("company_name"), "round": ev.get("round"), "date": ev.get("event_date", "")[:10]})
    # Sort and limit
    ranked = sorted(inv_stats.items(), key=lambda x: -x[1]["deal_count"])[:limit]
    # Check followed
    with get_db_ctx() as conn:
        followed = set(r[0] for r in conn.execute("SELECT investor_name FROM followed_investors WHERE user_id=?", (username,)).fetchall())
    result = []
    for name, s in ranked:
        result.append({"name": name, "deal_count": s["deal_count"], "lead_count": s["lead_count"], "total_amount": s["total_amount"], "recent_deals": s["deals"], "followed": name in followed})
    return jsonify({"investors": result, "total": len(inv_stats)})


@app.route("/api/investment/investors/follow", methods=["POST"])
def follow_investor():
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    body = request.get_json(force=True)
    name = body.get("investor_name", "").strip()
    if not name:
        return jsonify({"error": "investor_name required"}), 400
    with get_db_ctx() as conn:
        conn.execute("INSERT OR IGNORE INTO followed_investors (user_id, investor_name) VALUES (?,?)", (username, name))
        conn.commit()
    return jsonify({"message": "已关注", "investor_name": name})


@app.route("/api/investment/investors/unfollow", methods=["POST"])
def unfollow_investor():
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    body = request.get_json(force=True)
    name = body.get("investor_name", "").strip()
    with get_db_ctx() as conn:
        conn.execute("DELETE FROM followed_investors WHERE user_id=? AND investor_name=?", (username, name))
        conn.commit()
    return jsonify({"message": "已取消关注"})


# === 改进3: 投融资-赛道热度相关性 ===
@app.route("/api/investment/track-correlation", methods=["GET"])
def investment_track_correlation():
    """融资事件密度与赛道热度的相关性分析"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    days = request.args.get("days", 30, type=int)
    from datetime import date, timedelta
    start = (date.today() - timedelta(days=days)).isoformat()
    # Get investment events
    inv_data, inv_code = agent_request("GET", f"/api/itjuzi/events?start_date={start}&page_size=200")
    if inv_code != 200:
        return jsonify({"error": "投融资数据不可用"}), 502
    items = inv_data.get("items", [])
    # Get track heat
    heat_data, heat_code = agent_request("GET", "/api/tracks/heat?days=" + str(days))
    heat_latest, _ = agent_request("GET", "/api/tracks/heat/latest")
    tracks_info, _ = agent_request("GET", "/api/tracks")
    # Count investment events per industry
    from collections import defaultdict
    ind_count = defaultdict(int)
    ind_amount = defaultdict(float)
    for ev in items:
        ind = ev.get("industry") or "其他"
        ind_count[ind] += 1
        ind_amount[ind] += float(ev.get("amount_cny_est") or 0)
    # Build correlation data: match tracks to industries
    track_map = {}  # track_name -> latest_score
    if isinstance(heat_latest, list):
        for t in heat_latest:
            track_map[t.get("name", "")] = t.get("score", 0)
    elif isinstance(tracks_info, list):
        for t in tracks_info:
            track_map[t.get("name", "")] = 0
    # Correlation pairs
    correlations = []
    for ind, count in sorted(ind_count.items(), key=lambda x: -x[1]):
        score = track_map.get(ind, 0)
        correlations.append({
            "industry": ind,
            "event_count": count,
            "total_amount": ind_amount[ind],
            "heat_score": score,
            "density": round(count / max(days, 1) * 7, 1)  # events per week
        })
    # Summary insight
    hot_funded = [c for c in correlations if c["heat_score"] > 60 and c["event_count"] > 3]
    cold_funded = [c for c in correlations if c["heat_score"] < 40 and c["event_count"] > 3]
    return jsonify({
        "correlations": correlations,
        "summary": {
            "total_events": len(items),
            "tracked_industries": len(correlations),
            "hot_and_funded": [c["industry"] for c in hot_funded],
            "cold_but_funded": [c["industry"] for c in cold_funded],
        },
        "days": days
    })


# === 改进4: 推荐偏好设置 ===
@app.route("/api/recommendation/preferences", methods=["GET"])
def get_rec_preferences():
    """获取用户推荐偏好"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    defaults = {"style": "balanced", "risk_tolerance": "medium", "focus_dimensions": ["technical", "trend", "fundamental", "volume"], "min_score": 60}
    with get_db_ctx() as conn:
        row = conn.execute("SELECT value FROM user_preferences WHERE user_id=? AND key='rec_preferences'", (username,)).fetchone()
    if row:
        import json as _json
        try:
            prefs = _json.loads(row[0])
            if isinstance(prefs, dict):
                defaults.update(prefs)
        except Exception:
            pass
    return jsonify(defaults)


@app.route("/api/recommendation/preferences", methods=["PUT"])
def set_rec_preferences():
    """设置用户推荐偏好"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    body = request.get_json(force=True)
    allowed_styles = ["technical", "fundamental", "momentum", "balanced"]
    style = body.get("style", "balanced")
    if style not in allowed_styles:
        style = "balanced"
    prefs = {
        "style": style,
        "risk_tolerance": body.get("risk_tolerance", "medium"),
        "focus_dimensions": body.get("focus_dimensions", ["technical", "trend", "fundamental", "volume"]),
        "min_score": body.get("min_score", 60)
    }
    import json as _json
    prefs_json = _json.dumps(prefs, ensure_ascii=False)
    with get_db_ctx() as conn:
        existing = conn.execute("SELECT 1 FROM user_preferences WHERE user_id=? AND key='rec_preferences'", (username,)).fetchone()
        if existing:
            conn.execute("UPDATE user_preferences SET value=?, updated_at=datetime('now') WHERE user_id=? AND key='rec_preferences'", (prefs_json, username))
        else:
            conn.execute("INSERT INTO user_preferences (user_id, key, value) VALUES (?,'rec_preferences',?)", (username, prefs_json))
        conn.commit()
    return jsonify({"message": "偏好已保存", "preferences": prefs})


@app.route("/api/recommendation/hit-rate", methods=["GET"])
def rec_hit_rate_dashboard():
    """推荐命中率实时看板"""
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    days = request.args.get("days", 30, type=int)
    from datetime import date, timedelta
    start = (date.today() - timedelta(days=days)).isoformat()
    with get_db_ctx() as conn:
        rows = conn.execute(
            "SELECT rec_date, stock_code, stock_name, rec_score, technical_score, trend_score, fundamental_score, volume_score, return_t1, return_t3, return_t5, return_t10 "
            "FROM recommendation_history WHERE rec_date >= ? ORDER BY rec_date DESC", (start,)
        ).fetchall()
    if not rows:
        return jsonify({"message": "数据积累中", "days": days, "total": 0, "hit_rates": {}, "dimension_rates": {}, "daily_performance": []})
    # Calculate hit rates for each T+N
    from collections import defaultdict
    hit_rates = {}
    for col_idx, label in [(8,"t1"),(9,"t3"),(10,"t5"),(11,"t10")]:
        vals = [r[col_idx] for r in rows if r[col_idx] is not None]
        if vals:
            wins = sum(1 for v in vals if v > 0)
            hit_rates[label] = {"win": wins, "total": len(vals), "rate": round(wins/len(vals)*100, 1), "avg_return": round(sum(vals)/len(vals), 2)}
    # Dimension analysis (t5 only)
    dim_rates = {}
    t5_rows = [(r[4],r[5],r[6],r[7],r[10]) for r in rows if r[10] is not None]  # tech,trend,fund,vol,ret_t5
    dim_names = ["technical", "trend", "fundamental", "volume"]
    for i, dname in enumerate(dim_names):
        # Top quartile by dimension score
        sorted_by_dim = sorted(t5_rows, key=lambda x: x[i] or 0, reverse=True)
        top_q = sorted_by_dim[:max(1, len(sorted_by_dim)//4)]
        if top_q:
            wins = sum(1 for r in top_q if r[4] and r[4] > 0)
            dim_rates[dname] = {"rate": round(wins/len(top_q)*100, 1), "count": len(top_q), "avg_return": round(sum(r[4] for r in top_q if r[4])/max(1,len([r for r in top_q if r[4] is not None])), 2)}
    # Daily performance (grouped by date)
    daily = defaultdict(list)
    for r in rows:
        if r[10] is not None:
            daily[r[0]].append(r[10])
    daily_perf = [{"date": d, "avg_return": round(sum(vs)/len(vs), 2), "win_rate": round(sum(1 for v in vs if v>0)/len(vs)*100, 1), "count": len(vs)} for d, vs in sorted(daily.items())]
    return jsonify({
        "days": days,
        "total": len(rows),
        "evaluated": len([r for r in rows if r[10] is not None]),
        "hit_rates": hit_rates,
        "dimension_rates": dim_rates,
        "daily_performance": daily_perf
    })

# === 推荐回溯 API ===
@app.route("/api/recommendation/history", methods=["GET"])
def rec_history():
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    days = request.args.get("days", 30, type=int)
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    from datetime import date, timedelta
    start_date = (date.today() - timedelta(days=days)).isoformat()
    with get_db_ctx() as conn:
        total = conn.execute("SELECT count(*) FROM recommendation_history WHERE rec_date >= ?", (start_date,)).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM recommendation_history WHERE rec_date >= ? ORDER BY rec_date DESC, rec_score DESC LIMIT ? OFFSET ?",
            (start_date, page_size, (page-1)*page_size)
        ).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM recommendation_history LIMIT 0").description] if rows else []
    items = []
    for r in rows:
        item = dict(zip(cols, r))
        rt5 = item.get("return_t5")
        item["win"] = True if rt5 and rt5 > 0 else (False if rt5 is not None and rt5 <= 0 else None)
        items.append(item)
    return jsonify({"items": items, "total": total})


@app.route("/api/recommendation/stats", methods=["GET"])
def rec_stats():
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    days = request.args.get("days", 30, type=int)
    from datetime import date, timedelta
    start_date = (date.today() - timedelta(days=days)).isoformat()
    with get_db_ctx() as conn:
        total = conn.execute("SELECT count(*) FROM recommendation_history WHERE rec_date >= ?", (start_date,)).fetchone()[0]
        t5_rows = conn.execute("SELECT return_t5 FROM recommendation_history WHERE rec_date >= ? AND return_t5 IS NOT NULL", (start_date,)).fetchall()
        t5_vals = [r[0] for r in t5_rows]
        win_count = sum(1 for v in t5_vals if v > 0)
        win_rate = (win_count / len(t5_vals) * 100) if t5_vals else 0
        avg_ret = (sum(t5_vals) / len(t5_vals)) if t5_vals else 0
        best = conn.execute("SELECT stock_code, stock_name, rec_date, return_t5 FROM recommendation_history WHERE rec_date >= ? AND return_t5 IS NOT NULL ORDER BY return_t5 DESC LIMIT 1", (start_date,)).fetchone()
    best_pick = {"stock_code": best[0], "stock_name": best[1], "date": best[2], "return_t5": best[3]} if best else None
    return jsonify({
        "total_recommendations": total,
        "win_rate_t5": round(win_rate, 1),
        "avg_return_t5": round(avg_ret, 2),
        "best_pick": best_pick,
        "data_days": days,
        "evaluated_count": len(t5_vals)
    })


@app.route("/api/recommendation/backfill", methods=["POST"])
def rec_backfill_trigger():
    username = session.get("username", "")
    if not username:
        return jsonify({"error": "未登录"}), 401
    from datetime import date, timedelta
    today = date.today().isoformat()
    filled = 0
    with get_db_ctx() as conn:
        for offset, col_price, col_ret in [(1,"price_t1","return_t1"),(3,"price_t3","return_t3"),(5,"price_t5","return_t5"),(10,"price_t10","return_t10")]:
            target_date = (date.today() - timedelta(days=offset)).isoformat()
            rows = conn.execute(f"SELECT id, stock_code, price_at_rec FROM recommendation_history WHERE rec_date=? AND {col_price} IS NULL", (target_date,)).fetchall()
            for rid, code, par in rows:
                try:
                    qdata, qcode = shark_request("GET", f"/api/stock/quote?symbol={code}")
                    price = qdata.get("close") or qdata.get("current_price") or qdata.get("price")
                    if price and par:
                        ret = (float(price) - float(par)) / float(par) * 100
                        conn.execute(f"UPDATE recommendation_history SET {col_price}=?, {col_ret}=? WHERE id=?", (price, round(ret,2), rid))
                        filled += 1
                except Exception:
                    pass
        conn.commit()
    return jsonify({"filled": filled})



@app.route("/api/chanlun/czsc/history", methods=["GET"])
def chanlun_czsc_history():
    import pymysql
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    code = request.args.get("code", "")
    limit = request.args.get("limit", 200, type=int)

    DB = {"host":"127.0.0.1","port":3306,"user":"root","password":"password","database":"stock_analysis_system","charset":"utf8mb4"}
    try:
        conn = pymysql.connect(**DB)
        cur = conn.cursor(pymysql.cursors.DictCursor)

        query = "SELECT signal_date, code, name, type, price, stop_loss, score, grade, reason, trend_type, weekly_trend, divergence, div_ratio, market_attitude, market_env_score, seg_zg, seg_zd, entry_price, profile FROM czsc_signal_history WHERE 1=1"
        params = []

        if start_date:
            query += " AND signal_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND signal_date <= %s"
            params.append(end_date)
        if code:
            query += " AND code = %s"
            params.append(code)

        query += " ORDER BY signal_date DESC, score DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        signals = cur.fetchall()

        cur.execute("SELECT DISTINCT signal_date FROM czsc_signal_history ORDER BY signal_date DESC LIMIT 30")
        available_dates = [str(r["signal_date"]) for r in cur.fetchall()]

        conn.close()
        return jsonify({"signals": signals, "available_dates": available_dates, "count": len(signals)})
    except Exception as e:
        return jsonify({"error": str(e), "signals": [], "available_dates": []})
@app.route("/api/pipeline/status", methods=["GET"])
def pipeline_status_public():
    """Public endpoint: daily pipeline effort status (no auth required)."""
    from datetime import datetime as _dt
    import subprocess as _sp
    import sqlite3 as _s3

    result = {"timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S")}

    # 1. Pipeline daemon status
    try:
        ps_r = _sp.run(['ps','aux'], capture_output=True, text=True, timeout=5)
        daemon_alive = any('pipeline.py' in l and '--mode daemon' in l and 'grep' not in l for l in ps_r.stdout.split('\n'))
        daily_running = any('pipeline.py' in l and '--mode daily' in l and 'grep' not in l for l in ps_r.stdout.split('\n'))
        result["pipeline"] = {"daemon_alive": daemon_alive, "daily_running": daily_running}
    except Exception:
        result["pipeline"] = {"error": "check failed"}

    # 2. Data collection status
    try:
        with open('/var/log/d8q/data_status.json','r') as f:
            result["data"] = json.load(f)
    except Exception:
        result["data"] = {}

    # 3. CZSC scan status
    try:
        with open('/var/log/d8q/czsc_scan_status.json','r') as f:
            result["scan"] = json.load(f)
    except Exception:
        result["scan"] = {}

    # 4. Recent system events (last 24h, max 20)
    try:
        db_path = '/home/ecs-assist-user/d8q-data-agent/data/financial_news.db'
        since = (_dt.now(). _dt.now()).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        since = ''
    try:
        from datetime import timedelta as _td
        since = (_dt.now() - _td(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        db_path = '/home/ecs-assist-user/d8q-data-agent/data/financial_news.db'
        conn = _s3.connect(db_path)
        conn.row_factory = _s3.Row
        rows = [dict(r) for r in conn.execute(
            'SELECT event_type, component, severity, message, created_at '
            'FROM system_events WHERE created_at >= ? ORDER BY id DESC LIMIT 20', (since,)).fetchall()]
        conn.close()
        result["events"] = rows
    except Exception as e:
        result["events"] = []

    # 5. Today's signal count
    try:
        with open('/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/signals_cache_czsc.json','r') as f:
            sig_data = json.load(f)
        result["signals"] = {
            "generated_at": sig_data.get("generated_at"),
            "count": len(sig_data.get("today_signals", []))
        }
    except Exception:
        result["signals"] = {}

    return jsonify(result)


@app.route("/<path:path>")
def spa_fallback(path):
    """SPA 路由 fallback — 所有非 API/static 路由返回 index.html"""
    if path.startswith(("api/", "static/")):
        return jsonify({"error": "Not found"}), 404
    with open(os.path.join(TMPL_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


# === 企微推送（Webhook群机器人）===
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7c097c2e-d664-46e4-bbdc-39ff5bc1b537"


def _send_wecom_webhook(content, msgtype="markdown"):
    """Send message via WeCom group bot webhook"""
    body = {"msgtype": msgtype}
    if msgtype == "markdown":
        body["markdown"] = {"content": content}
    else:
        body["text"] = {"content": content}
    req = urllib.request.Request(
        WECOM_WEBHOOK_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


# === 缠论信号代理路由 ===
@app.route("/api/chanlun/signals", methods=["GET"])
def chanlun_signals():
    qs = request.query_string.decode()
    path = "/chanlun/signals" + ("?" + qs if qs else "")
    data, code = compass_request("GET", path)
    return jsonify(data), code


@app.route("/api/chanlun/signals/<stock_code>", methods=["GET"])
def chanlun_signal_detail(stock_code):
    data, code = compass_request("GET", "/chanlun/signals/%s" % stock_code)
    return jsonify(data), code


@app.route("/api/chanlun/backtest", methods=["GET"])
def chanlun_backtest():
    data, code = compass_request("GET", "/chanlun/backtest")
    return jsonify(data), code


@app.route("/api/chanlun/scan", methods=["POST"])
def chanlun_scan():
    data, code = compass_request("POST", "/chanlun/scan")
    return jsonify(data), code


@app.route("/api/chanlun/disciplined", methods=["GET"])
def chanlun_disciplined():
    """纪律化策略数据（读取缓存，每日15:37更新）"""
    from datetime import datetime as _dt
    
    signals_path = "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/signals_cache.json"
    holdings_path = "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/holdings.json"
    
    signals = []
    try:
        with open(signals_path, "r") as f:
            signals = json.load(f)
    except Exception:
        pass
    
    holdings = []
    try:
        with open(holdings_path, "r") as f:
            holdings = json.load(f)
    except Exception:
        pass
    
    config = {
        "risk_preference": "balanced",
        "stop_loss_pct": 0.05,
        "trailing_trigger": 0.08,
        "trailing_drawdown": 0.03,
        "max_hold_days": 10,
        "full_position": 10000,
        "max_holdings": 3,
    }
    
    return jsonify({
        "date": _dt.now().strftime("%Y-%m-%d"),
        "signals": signals,
        "holdings": holdings,
        "config": config,
    }), 200



@app.route("/api/chanlun/czsc", methods=["GET"])
def chanlun_czsc():
    import json as _json, os as _os
    path = "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/signals_cache_czsc.json"
    try:
        if _os.path.exists(path):
            with open(path) as f:
                d = _json.load(f)
            return jsonify(d)
        return jsonify({"signals": [], "engine": "czsc", "signal_count": 0})
    except Exception as e:
        return jsonify({"error": str(e), "signals": []})



@app.route("/api/chanlun/czsc/<stock_code>", methods=["GET"])
def chanlun_czsc_detail(stock_code):
    import subprocess, json as _json
    try:
        cmd = ["/home/ecs-assist-user/d8q-intelligentengine-stockcompass/venv/bin/python",
               "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/czsc_detail_cli.py",
               stock_code]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return jsonify(_json.loads(r.stdout))
        return jsonify({"error": r.stderr[:500]})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/chanlun/review", methods=["GET"])
def chanlun_review():
    """复盘统计API"""
    import json as _json, os as _os
    path = "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/review_stats.json"
    try:
        if _os.path.exists(path):
            with open(path) as f:
                d = _json.load(f)
            return jsonify(d)
        return jsonify({"total": 0, "message": "暂无复盘数据"})
    except Exception as e:
        return jsonify({"error": str(e), "total": 0})

@app.route("/api/chanlun/notify", methods=["POST"])
def chanlun_notify():
    """企微群机器人推送缠论信号"""
    body = request.json or {}
    content = body.get("content", "")
    if not content:
        return jsonify({"status": "error", "message": "content required"}), 400
    msgtype = body.get("msgtype", "markdown")
    try:
        result = _send_wecom_webhook(content=content, msgtype=msgtype)
        if result.get("errcode") == 0:
            return jsonify({"status": "ok", "message": "pushed"}), 200
        else:
            return jsonify({"status": "error", "message": result.get("errmsg", ""), "errcode": result.get("errcode")}), 502
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
