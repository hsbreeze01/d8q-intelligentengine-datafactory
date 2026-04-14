"""D8Q 智能资讯工厂 - 前后端一体 Web 应用 v2 (含任务管理)"""
import sqlite3, json, os
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)
DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"
AGENT_API = "http://localhost:8000"
SHARK_API = "http://localhost:5000"
TMPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
def index():
    with open(os.path.join(TMPL_DIR, "news.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/tasks")
def tasks_page():
    with open(os.path.join(TMPL_DIR, "tasks.html"), encoding="utf-8") as f:
        return f.read()


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
    where, params = [], []
    if subject:
        where.append("subject=?"); params.append(subject)
    if source:
        where.append("source=?"); params.append(source)
    if date:
        where.append("DATE(publish_time)=?"); params.append(date)
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



def shark_request(method, path, data=None):
    """Proxy request to StockShark API"""
    url = SHARK_API + urllib.parse.quote(path, safe='/:?=&')
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code
    except Exception as e:
        return {"error": str(e)}, 502


@app.route("/stock")
def stock_page():
    with open(os.path.join(TMPL_DIR, "stock.html"), encoding="utf-8") as f:
        return f.read()


# --- Stock Analysis API (proxy to StockShark) ---
@app.route("/api/stock/comprehensive", methods=["POST"])
def stock_comprehensive():
    data, code = shark_request("POST", "/api/analysis/stock/comprehensive", request.json)
    return jsonify(data), code


@app.route("/api/stock/announcements", methods=["GET"])
def stock_announcements():
    sc = request.args.get("stock_code", "")
    days = request.args.get("days", "30")
    data, status = shark_request("GET", "/api/announcement/stock/" + sc + "?days=" + days)
    return jsonify(data), status


@app.route("/api/stock/reports", methods=["GET"])
def stock_reports():
    keyword = request.args.get("keyword", "")
    data, status = shark_request("GET", "/api/report/search?keyword=" + keyword + "&limit=20")
    return jsonify(data), status


@app.route("/api/stock/quote", methods=["GET"])
def stock_quote():
    symbol = request.args.get("symbol", "")
    data, status = shark_request("GET", "/api/analysis/stock/quote?symbol=" + symbol)
    return jsonify(data), status



@app.route("/report")
def report_page():
    with open(os.path.join(TMPL_DIR, "report.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/api/report/stock", methods=["POST"])
def report_stock_query():
    """批量查询股票研报 - 代理到 StockShark"""
    body = request.json or {}
    keywords = body.get("keywords", [])
    days = body.get("days", 7)
    results = []
    for kw in keywords[:20]:  # 限制最多20个
        data, code = shark_request("GET", "/api/report/stock/" + kw + "?days=" + str(days) + "&stock_name=" + kw)
        if code == 200:
            results.append(data)
        else:
            results.append({"stock_code": kw, "stock_name": kw, "reports": [], "announcements": [], "error": str(data)})
    return jsonify({"results": results}), 200



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


@app.route("/api/content/tasks/<task_id>/run", methods=["POST"])
def run_content_task(task_id):
    tasks = _load_content_tasks()
    task = next((t for t in tasks if t.get("id") == task_id), None)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    task_type = task.get("type", "creation")
    if task_type == "creation":
        from datafactory.content.creator import create_article
        result = create_article(
            task.get("subject", ""),
            style=task.get("style", "news_brief"),
            freq=task.get("freq", "daily"),
        )
        return jsonify(result), 200
    elif task_type == "publish":
        # 读取最新文章并返回发布数据
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
                        content = f.read()
                    return jsonify({
                        "status": "ready",
                        "subject": subject,
                        "file": files[-1],
                        "content_preview": content[:500],
                        "channel": task.get("channel", "xiaohongshu"),
                    }), 200
        return jsonify({"error": "无文章可发布"}), 404

    return jsonify({"error": "未知任务类型"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)
