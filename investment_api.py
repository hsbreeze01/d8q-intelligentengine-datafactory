"""投融资数据代理 API Blueprint - 转发到 dataagent (localhost:8000)"""
import json
import os
import urllib.request
import urllib.parse
from flask import Blueprint, request, jsonify

investment_bp = Blueprint("investment", __name__)

AGENT_API = os.environ.get("DATAAGENT_BASE_URL", "http://localhost:8000")
TMPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _agent_get(path, params=None, timeout=30):
    """GET request to agent API"""
    url = AGENT_API + path
    if params:
        qs = urllib.parse.urlencode(params, doseq=True)
        url += "?" + qs
    req = urllib.request.Request(url, method="GET")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw), e.code
        except (json.JSONDecodeError, ValueError):
            return {"error": f"HTTP {e.code}"}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


def _agent_post(path, data=None, timeout=60):
    """POST request to agent API"""
    url = AGENT_API + path
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw), e.code
        except (json.JSONDecodeError, ValueError):
            return {"error": f"HTTP {e.code}"}, e.code
    except Exception as e:
        return {"error": str(e)}, 502



# === 代理 API ===
@investment_bp.route("/api/investment/events", methods=["GET"])
def proxy_investment_events():
    """代理投融资事件列表"""
    params = dict(request.args)
    data, code = _agent_get("/api/itjuzi/events", params)
    return jsonify(data), code


@investment_bp.route("/api/investment/events/<int:event_id>", methods=["GET"])
def proxy_investment_event_detail(event_id):
    """代理投融资事件详情"""
    data, code = _agent_get(f"/api/itjuzi/events/{event_id}")
    return jsonify(data), code


@investment_bp.route("/api/investment/material", methods=["GET"])
def proxy_investment_material():
    """代理新材料投融资两层查询"""
    params = dict(request.args)
    data, code = _agent_get("/api/itjuzi/material", params)
    return jsonify(data), code


@investment_bp.route("/api/investment/stats", methods=["GET"])
def proxy_investment_stats():
    """代理投融资统计"""
    params = dict(request.args)
    data, code = _agent_get("/api/itjuzi/stats", params)
    return jsonify(data), code


@investment_bp.route("/api/investment/collect/<source>", methods=["POST"])
def proxy_investment_collect(source):
    """代理手动触发采集"""
    if source not in ("kr36", "pedaily"):
        return jsonify({"error": "不支持的数据源"}), 400
    body = request.get_json(silent=True) or {}
    data, code = _agent_post(f"/api/itjuzi/collect/{source}", body)
    return jsonify(data), code
