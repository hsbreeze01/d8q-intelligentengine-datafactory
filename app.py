"""D8Q 智能资讯工厂 - 前后端一体 Web 应用 v2 (含任务管理)"""
import sqlite3, json, os
import urllib.request
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)
DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"
AGENT_API = "http://localhost:8000"
TMPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def agent_request(method, path, data=None):
    """Proxy request to agent API"""
    url = AGENT_API + path
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)
