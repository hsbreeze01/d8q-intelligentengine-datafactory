"""认证与权限管控模块"""
import json, os, time, bcrypt, secrets
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, session, jsonify, redirect

auth_bp = Blueprint("auth", __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

# --- 角色权限 ---
ROLE_PERMS = {
    "viewer": {"read"},
    "editor": {"read", "write", "execute"},
    "admin":  {"read", "write", "execute", "admin"},
}

# 写入/管理操作的权限要求 (method, path_prefix) → permission
WRITE_ROUTES = [
    (("POST",),   "/api/content/create",  "write"),
    (("POST",),   "/api/content/tasks",   "write"),
    (("DELETE",),  "/api/content/tasks/",  "write"),
    (("POST",),   "/api/content/tasks/",  "execute"),  # run, toggle
    (("PUT",),    "/api/llm-config",      "admin"),
    (("PUT",),    "/api/keyword-suggestions", "admin"),
    (("GET",),    "/settings",            "admin"),
    (("POST","DELETE","PUT","GET"), "/api/auth/users", "admin"),
]

PUBLIC_PATHS = {"/login", "/api/auth/login"}
INTERNAL_IPS = {"127.0.0.1"}

# --- 登录限流 ---
_fail_counts = {}  # ip → (count, first_fail_time)
MAX_FAILS, LOCKOUT_SECS = 5, 900


def _load_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_pw(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_pw(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _is_locked(ip):
    if ip not in _fail_counts:
        return False
    count, first = _fail_counts[ip]
    if time.time() - first > LOCKOUT_SECS:
        del _fail_counts[ip]
        return False
    return count >= MAX_FAILS


def _record_fail(ip):
    now = time.time()
    if ip in _fail_counts:
        count, first = _fail_counts[ip]
        if now - first > LOCKOUT_SECS:
            _fail_counts[ip] = (1, now)
        else:
            _fail_counts[ip] = (count + 1, first)
    else:
        _fail_counts[ip] = (1, now)


def _get_required_perm(method, path):
    for methods, prefix, perm in WRITE_ROUTES:
        if method in methods and path.startswith(prefix):
            return perm
    return None


# --- before_request 拦截器（由 app.py 注册） ---
def check_auth():
    # 内部调用放行
    if request.remote_addr in INTERNAL_IPS:
        return
    # 公开路由放行
    if request.path in PUBLIC_PATHS:
        return
    # 静态资源放行
    if request.path.startswith("/static"):
        return
    # 检查 session
    if "username" not in session:
        if request.path.startswith("/api/"):
            return jsonify({"error": "未登录"}), 401
        return redirect("/login")
    # 权限检查
    required = _get_required_perm(request.method, request.path)
    if required:
        role = session.get("role", "viewer")
        if required not in ROLE_PERMS.get(role, set()):
            if request.path.startswith("/api/"):
                return jsonify({"error": "权限不足"}), 403
            return "权限不足", 403


# --- API 路由 ---
@auth_bp.route("/login")
def login_page():
    tmpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "login.html")
    with open(tmpl, encoding="utf-8") as f:
        return f.read()


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    ip = request.remote_addr
    if _is_locked(ip):
        return jsonify({"error": "登录失败次数过多，请15分钟后重试"}), 429

    body = request.json or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")

    users = _load_users()
    user = next((u for u in users if u["username"] == username), None)

    if not user or not _check_pw(password, user["password_hash"]):
        _record_fail(ip)
        return jsonify({"error": "用户名或密码错误"}), 401

    # 清除失败计数
    _fail_counts.pop(ip, None)
    # 写入 session
    session.permanent = True
    session.clear()
    session["username"] = user["username"]
    session["role"] = user.get("role", "viewer")
    return jsonify({"ok": True, "username": user["username"], "role": user["role"]})


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/api/auth/me")
def me():
    if "username" not in session:
        return jsonify({"error": "未登录"}), 401
    return jsonify({"username": session["username"], "role": session["role"]})


@auth_bp.route("/api/auth/users", methods=["GET"])
def list_users():
    users = _load_users()
    return jsonify([{"username": u["username"], "role": u["role"],
                     "created_at": u.get("created_at", "")} for u in users])


@auth_bp.route("/api/auth/users", methods=["POST"])
def create_user():
    body = request.json or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")
    role = body.get("role", "viewer")
    if not username or not password:
        return jsonify({"error": "用户名和密码必填"}), 400
    if len(password) < 8:
        return jsonify({"error": "密码至少8位"}), 400
    if role not in ROLE_PERMS:
        return jsonify({"error": "无效角色"}), 400

    users = _load_users()
    if any(u["username"] == username for u in users):
        return jsonify({"error": "用户已存在"}), 409

    users.append({
        "username": username,
        "password_hash": _hash_pw(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
    })
    _save_users(users)
    return jsonify({"ok": True, "username": username, "role": role}), 201


@auth_bp.route("/api/auth/users/<username>", methods=["DELETE"])
def delete_user(username):
    if username == session.get("username"):
        return jsonify({"error": "不能删除自己"}), 400
    users = [u for u in _load_users() if u["username"] != username]
    _save_users(users)
    return jsonify({"ok": True})


@auth_bp.route("/api/auth/users/<username>/password", methods=["PUT"])
def change_password(username):
    # admin 可改任何人，普通用户只能改自己
    if session.get("role") != "admin" and session.get("username") != username:
        return jsonify({"error": "权限不足"}), 403
    body = request.json or {}
    password = body.get("password", "")
    if len(password) < 8:
        return jsonify({"error": "密码至少8位"}), 400
    users = _load_users()
    for u in users:
        if u["username"] == username:
            u["password_hash"] = _hash_pw(password)
            _save_users(users)
            return jsonify({"ok": True})
    return jsonify({"error": "用户不存在"}), 404
