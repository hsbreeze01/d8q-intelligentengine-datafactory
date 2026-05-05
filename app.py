"""D8Q 智能资讯工厂 - 前后端一体 Web 应用 v2 (含任务管理)"""
import sqlite3, json, os
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify, render_template_string, send_from_directory, session
import time as _time

app = Flask(__name__)

# --- 认证与权限 ---
import secrets
from datetime import timedelta
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
from auth import auth_bp, check_auth, INTERNAL_IPS
app.register_blueprint(auth_bp)
app.before_request(check_auth)

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
        conn = get_db()
        conn.execute(
            "INSERT INTO user_events (user_id, event_time, function_name, method, path, status_code, duration_ms) VALUES (?, datetime('now'), ?, ?, ?, ?, ?)",
            (username, func_name, request.method, path, response.status_code, duration)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    _cleanup_old_events()
    return response

from export_weekly import export_bp
from prompts_api import bp as prompts_bp
app.register_blueprint(export_bp)
app.register_blueprint(prompts_bp)
DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"
AGENT_API = "http://localhost:8000"
SHARK_API = "http://localhost:5000"
PUBLISHER_API = "http://localhost:8089"
TMPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
}


def _init_monitor_tables():
    conn = get_db()
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
    conn.close()


def _classify_function(path):
    for prefix in sorted(FUNCTION_MAP.keys(), key=len, reverse=True):
        if path.startswith(prefix):
            return FUNCTION_MAP[prefix]
    return "其他"

def _init_events_table():
    conn = get_db()
    conn.execute("PRAGMA journal_mode=WAL")
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
    conn.close()

try:
    _init_events_table()
    _init_monitor_tables()
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
        conn = get_db()
        conn.execute("DELETE FROM user_events WHERE event_time < datetime('now', '-90 days')")
        conn.commit()
        conn.close()
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
        return json.loads(e.read()), e.code
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
def index():
    with open(os.path.join(TMPL_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/api/proxy/tracks", methods=["GET"])
@app.route("/api/proxy/tracks/heat", methods=["GET"])
@app.route("/api/proxy/tracks/heat/latest", methods=["GET"])
@app.route("/api/proxy/tracks/<int:track_id>/news", methods=["GET"])
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
        _conn = get_db()
        _has_subs = _conn.execute("SELECT 1 FROM user_subscriptions WHERE user_id=? LIMIT 1", (_username,)).fetchone()
        _conn.close()
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


@app.route("/api/weekly/generate", methods=["POST"])
def weekly_generate():
    """Generate weekly report via LLM"""
    from datafactory.content.llm_creator import _llm_call, _fetch_news
    body = request.json or {}
    track_id = body.get("track_id", 1)
    days = body.get("days", 7)
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    track = conn.execute("SELECT name FROM tracks WHERE id=?", (track_id,)).fetchone()
    if not track:
        conn.close()
        return jsonify({"error": "赛道不存在"}), 404
    track_name = track["name"]
    conn.close()
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
    conn = get_db()
    try:
        subjects = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM financial_news ORDER BY subject")]
        sources = [r[0] for r in conn.execute("SELECT DISTINCT source FROM financial_news ORDER BY source")]
        return jsonify({"subjects": subjects, "sources": sources})
    finally:
        conn.close()


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
        where.append("subject=?"); params.append(subject)
    if source:
        where.append("source=?"); params.append(source)
    if date:
        where.append("DATE(publish_time)=?"); params.append(date)
    if keyword:
        where.append("(title LIKE ? OR entities LIKE ?)"); params.extend(['%'+keyword+'%', '%'+keyword+'%'])
    if news_type:
        where.append("news_type=?"); params.append(news_type)
    # User subscription filtering
    _news_username = session.get("username", "")
    _news_role = session.get("role", "viewer")
    _news_view = request.args.get("view", "")
    if _news_username and _news_view != "all":
        conn_u = get_db()
        try:
            _sub_rows = conn_u.execute(
                "SELECT t.name FROM user_subscriptions us JOIN tracks t ON us.track_id = t.id WHERE us.user_id = ?",
                (_news_username,)
            ).fetchall()
        finally:
            conn_u.close()
        if _sub_rows:
            _track_names = [r[0] for r in _sub_rows]
            _placeholders = ",".join(["?"] * len(_track_names))
            where.append(f"subject IN ({_placeholders})")
            params.extend(_track_names)
        # If no subscriptions, return full data (new user guidance)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    conn = get_db()
    try:
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
    finally:
        conn.close()


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
    """Edit = delete old + create new with same id"""
    agent_request("DELETE", "/api/tasks/" + task_id)
    body = request.json
    body["id"] = task_id
    # Agent POST /api/tasks auto-generates id, so we create via direct DB + reload
    # Simpler: just create new task (agent assigns new id)
    data, code = agent_request("POST", "/api/tasks", body)
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


def _publisher_request(method, path, data=None):
    """Proxy request to InfoPublisher API"""
    url = PUBLISHER_API + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code
    except Exception as e:
        return {"error": str(e)}, 502



import time as _time

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
        return json.loads(e.read()), e.code
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
import sys
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
            f.seek(0); f.truncate()
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
                    body = "\n".join(l for l in lines[1:] if not l.startswith(">") and l.strip())[:1000]
                    # 调用 infopublisher API
                    pub_data = {"platform": task.get("channel", "xiaohongshu"), "title": title, "content": body}
                    pub_result, pub_code = _publisher_request("POST", "/api/publish", pub_data)
                    pub_result["file"] = files[-1]
                    pub_result["subject"] = subject
                    _append_exec_log(task, pub_result, __import__("time").time() - _t0, request.args.get("trigger", "manual"))
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
    conn = get_db()
    row = conn.execute("SELECT * FROM push_configs WHERE user_id=?", (username,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"user_id": username, "email": "", "enabled_types": "[]",
                    "daily_time": "08:00", "weekly_day": "friday", "alert_threshold": 30})


@app.route("/api/push/config", methods=["PUT"])
def update_push_config():
    username = session.get("username", "")
    body = request.json or {}
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO push_configs "
        "(user_id, email, enabled_types, daily_time, weekly_day, alert_threshold, webhook_url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, body.get("email", ""), json.dumps(body.get("enabled_types", [])),
         body.get("daily_time", "08:00"), body.get("weekly_day", "friday"),
         body.get("alert_threshold", 30), body.get("webhook_url", "")))
    conn.commit()
    conn.close()
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
        "stockshark":    {"port": 5000, "path": "/health"},
        "compass":       {"port": 8087, "path": "/health"},
        "factory":       {"port": 8088, "path": "/"},
        "infopublisher": {"port": 8089, "path": "/api/publish", "method": "GET"},
    }
    for name, cfg in http_services.items():
        try:
            url = f"http://localhost:{cfg['port']}{cfg['path']}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                services[name] = {"status": "ok", "type": "http", "port": cfg["port"]}
        except urllib.error.HTTPError as e:
            # 405 = route exists (e.g. POST-only), service is alive
            if e.code == 405:
                services[name] = {"status": "ok", "type": "http", "port": cfg["port"]}
            else:
                services[name] = {"status": "ok" if e.code < 500 else "error", "type": "http", "port": cfg["port"], "code": e.code}
        except Exception:
            services[name] = {"status": "down", "type": "http", "port": cfg["port"]}

    # systemd 管理的基础服务
    for svc in ["xvfb", "ghost_browser"]:
        try:
            r = subprocess.run(["systemctl", "is-active", f"d8q-{svc.replace(chr(95),chr(45))}"],
                               capture_output=True, text=True, timeout=3)
            active = r.stdout.strip() == "active"
            entry = {"status": "active" if active else "inactive", "type": "systemd"}
            if svc == "ghost_browser" and active:
                try:
                    req = urllib.request.Request("http://localhost:9222/json/version", method="GET")
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        entry["cdp"] = "ok"
                except Exception:
                    entry["cdp"] = "down"
            services[svc] = entry
        except Exception:
            services[svc] = {"status": "unknown", "type": "systemd"}

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

    conn = get_db()
    track = conn.execute("SELECT name, keywords FROM tracks WHERE id=?", (track_id,)).fetchone()
    if not track:
        conn.close()
        return jsonify({"error": "赛道不存在"}), 404

    # 检查缓存（同一赛道同一天只调一次LLM）
    if not refresh:
        cache = conn.execute(
            "SELECT data FROM research_cache WHERE track_id=? AND date=?",
            (track_id, today)).fetchone()
        if cache:
            conn.close()
            result = json.loads(cache["data"])
            result["cached"] = True
            return jsonify(result)

    conn.close()

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
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO research_cache (track_id, date, data) VALUES (?,?,?)",
                (track_id, today, json.dumps(result, ensure_ascii=False)))
    conn.commit()
    conn.close()
    result["cached"] = False
    return jsonify(result)

# --- 运营分析 API (admin only) ---
@app.route("/api/analytics/overview")
def analytics_overview():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    conn = get_db()
    try:
        dau = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_events WHERE DATE(event_time)=DATE('now')").fetchone()[0]
        mau = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_events WHERE event_time >= datetime('now', '-30 days')").fetchone()[0]
        today_events = conn.execute("SELECT COUNT(*) FROM user_events WHERE DATE(event_time)=DATE('now')").fetchone()[0]
        top = conn.execute("SELECT function_name, COUNT(*) as c FROM user_events WHERE DATE(event_time)=DATE('now') GROUP BY function_name ORDER BY c DESC LIMIT 1").fetchone()
        return jsonify({"dau": dau, "mau": mau, "today_events": today_events,
            "top_function": {"name": top[0], "count": top[1]} if top else {"name": "-", "count": 0}})
    finally:
        conn.close()

@app.route("/api/analytics/functions")
def analytics_functions():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    conn = get_db()
    try:
        cutoff = "datetime('now', '-{} days')".format(days) if days < 9999 else "datetime('2000-01-01')"
        total = conn.execute("SELECT COUNT(*) FROM user_events WHERE event_time >= " + cutoff).fetchone()[0]
        rows = conn.execute("SELECT function_name, COUNT(*) as c FROM user_events WHERE event_time >= " + cutoff + " GROUP BY function_name ORDER BY c DESC").fetchall()
        return jsonify({"functions": [{"name": r[0], "count": r[1], "percentage": round(r[1]/max(total,1)*100, 1)} for r in rows], "total": total})
    finally:
        conn.close()

@app.route("/api/analytics/users")
def analytics_users():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    conn = get_db()
    try:
        cutoff = "datetime('now', '-{} days')".format(days) if days < 9999 else "datetime('2000-01-01')"
        rows = conn.execute("SELECT user_id, MAX(event_time) as last_active, COUNT(DISTINCT function_name) as func_count, COUNT(*) as total_calls, ROUND(CAST(COUNT(*) AS FLOAT) / MAX(julianday('now') - julianday(MIN(event_time)), 1), 1) as daily_avg FROM user_events WHERE event_time >= " + cutoff + " GROUP BY user_id ORDER BY total_calls DESC").fetchall()
        return jsonify({"users": [{"user_id": r[0], "last_active": r[1], "function_count": r[2], "total_calls": r[3], "daily_avg": r[4]} for r in rows]})
    finally:
        conn.close()

@app.route("/api/analytics/trends")
def analytics_trends():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    conn = get_db()
    try:
        rows = conn.execute("SELECT DATE(event_time) as date, COUNT(DISTINCT user_id) as dau, COUNT(*) as total_calls FROM user_events WHERE event_time >= datetime('now', '-{} days') GROUP BY DATE(event_time) ORDER BY date".format(days)).fetchall()
        return jsonify({"trends": [{"date": r[0], "dau": r[1], "total_calls": r[2]} for r in rows]})
    finally:
        conn.close()

@app.route("/api/analytics/cold-hot")
def analytics_cold_hot():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    days = int(request.args.get("days", 30))
    conn = get_db()
    try:
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
    finally:
        conn.close()


# 启动调度器（gunicorn preload模式下只启动一次）
from scheduler import start_scheduler
start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)


# --- 邮件推送 API ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        return jsonify(json.loads(e.read())), e.code
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
                return "error", f"锁文件已存在 {int(age)}秒", {"age_sec": int(age)}
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
    if rt == "http": return _execute_http_check(cfg)
    if rt == "system": return _execute_system_check(cfg)
    if rt == "custom": return _execute_custom_check(cfg)
    return "unknown", f"未知类型: {rt}", {}

@app.route("/api/monitor/rules", methods=["GET"])
def get_monitor_rules():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    conn = get_db()
    rules = [dict(r) for r in conn.execute("SELECT * FROM monitor_rules ORDER BY builtin DESC, id").fetchall()]
    conn.close()
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
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO monitor_rules (name,type,config_json,severity,enabled,builtin,interval_sec) VALUES (?,?,?,?,1,0,?)",
        (name, rtype, json.dumps(config), severity, interval_sec))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return jsonify({"id": rid, "success": True}), 201

@app.route("/api/monitor/rules/<int:rule_id>", methods=["PUT"])
def update_monitor_rule(rule_id):
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    body = request.json or {}
    conn = get_db()
    rule = conn.execute("SELECT * FROM monitor_rules WHERE id=?", (rule_id,)).fetchone()
    if not rule:
        conn.close()
        return jsonify({"error": "规则不存在"}), 404
    if rule["builtin"]:
        if "enabled" in body:
            conn.execute("UPDATE monitor_rules SET enabled=? WHERE id=?", (int(body["enabled"]), rule_id))
            conn.commit()
        conn.close()
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
    conn.close()
    return jsonify({"success": True})

@app.route("/api/monitor/rules/<int:rule_id>", methods=["DELETE"])
def delete_monitor_rule(rule_id):
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    conn = get_db()
    rule = conn.execute("SELECT builtin FROM monitor_rules WHERE id=?", (rule_id,)).fetchone()
    if not rule:
        conn.close()
        return jsonify({"error": "规则不存在"}), 404
    if rule["builtin"]:
        conn.close()
        return jsonify({"error": "内置规则不可删除"}), 403
    conn.execute("DELETE FROM monitor_rules WHERE id=?", (rule_id,))
    conn.execute("DELETE FROM monitor_results WHERE rule_id=?", (rule_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/monitor/status", methods=["GET"])
def monitor_status():
    if session.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    from datetime import datetime as _dt
    conn = get_db()
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
                        if dj: raw = json.loads(dj)
                    except Exception:
                        pass
                    rule_results.append({"rule_id": rule["id"], "name": rule["name"], "type": rule["type"],
                        "severity": rule["severity"], "status": st, "message": cached["message"], "checked_at": cached["checked_at"], "raw_data": raw})
                    if st != "ok": alert_count += 1
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
            if status != "ok": alert_count += 1
            rule_results.append({"rule_id": rule["id"], "name": rule["name"], "type": rule["type"],
                "severity": rule["severity"], "status": status, "message": message, "checked_at": checked_at, "raw_data": detail or {}})
    conn.close()
    import subprocess
    services = {}
    http_svcs = {"agent":{"port":8000,"path":"/api/health"},"stockshark":{"port":5000,"path":"/health"},
        "compass":{"port":8087,"path":"/health"},"factory":{"port":8088,"path":"/"},
        "infopublisher":{"port":8089,"path":"/api/publish"}}
    for name, cfg in http_svcs.items():
        start = _time.time()
        try:
            req = urllib.request.Request(f"http://localhost:{cfg['port']}{cfg['path']}", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                services[name] = {"status": "ok", "port": cfg["port"], "elapsed_ms": int((_time.time()-start)*1000)}
        except urllib.error.HTTPError as e:
            elapsed = int((_time.time()-start)*1000)
            if e.code == 405:
                services[name] = {"status": "ok", "port": cfg["port"], "elapsed_ms": elapsed}
            else:
                services[name] = {"status": "ok" if e.code < 500 else "error", "port": cfg["port"], "elapsed_ms": elapsed}
                if e.code >= 500: alert_count += 1
        except Exception:
            services[name] = {"status": "down", "port": cfg["port"]}
            alert_count += 1
    for svc in ["xvfb", "ghost_browser"]:
        try:
            r = subprocess.run(["systemctl", "is-active", f"d8q-{svc.replace('_','-')}"], capture_output=True, text=True, timeout=3)
            active = r.stdout.strip() == "active"
            entry = {"status": "active" if active else "inactive", "type": "systemd"}
            if not active: alert_count += 1
            if svc == "ghost_browser" and active:
                try:
                    start = _time.time()
                    req = urllib.request.Request("http://localhost:9222/json/version", method="GET")
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        entry["cdp"] = "ok"
                        entry["elapsed_ms"] = int((_time.time()-start)*1000)
                except Exception:
                    entry["cdp"] = "down"
            services[svc] = entry
        except Exception:
            services[svc] = {"status": "unknown", "type": "systemd"}
    return jsonify({"services": services, "rules": rule_results, "alert_count": alert_count,
        "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S")})


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
        return jsonify(json.loads(e.read())), e.code
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
    except urllib.error.HTTPError as e:
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
        return jsonify(json.loads(e.read())), e.code
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
        return jsonify(json.loads(e.read())), e.code
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
        return jsonify(json.loads(e.read())), e.code
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
        return jsonify(json.loads(e.read())), e.code
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500
