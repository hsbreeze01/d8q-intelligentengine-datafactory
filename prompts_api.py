"""Factory Prompt 管理 API — 管理本地 + 聚合所有服务 prompts"""
import json
import os
import sys
import urllib.request
from flask import Blueprint, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_loader import PromptManager

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts')
pm = PromptManager(PROMPTS_DIR)

bp = Blueprint('prompts', __name__)

SERVICES = {
    'agent': 'http://localhost:8000/api/llm/prompts',
    'shark': 'http://localhost:5000/api/prompts/',
    'compass': 'http://localhost:8087/api/prompts',
}


@bp.route('/api/prompts', methods=['GET'])
def list_prompts():
    """列出 Factory 本地 prompts"""
    return jsonify({"success": True, "prompts": pm.list_all(), "service": "factory"})


@bp.route('/api/prompts/<path:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    p = pm.get(prompt_id)
    if p:
        return jsonify({"success": True, "prompt": p})
    return jsonify({"success": False, "error": "Prompt not found"}), 404


@bp.route('/api/prompts/<path:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    body = request.json or {}
    if pm.save(prompt_id, body):
        return jsonify({"success": True, "message": "Prompt updated"})
    return jsonify({"success": False, "error": "Save failed"}), 500


@bp.route('/api/prompts/all', methods=['GET'])
def list_all_services():
    """聚合所有服务的 prompts"""
    result = {"factory": pm.list_all()}
    for name, url in SERVICES.items():
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                result[name] = data.get("prompts", {})
        except Exception:
            result[name] = {"error": "unavailable"}
    return jsonify({"success": True, "services": result})


@bp.route('/api/prompts/<service>/<path:prompt_id>', methods=['PUT'])
def update_remote_prompt(service, prompt_id):
    """代理更新远程服务的 prompt"""
    if service not in SERVICES:
        return jsonify({"success": False, "error": f"Unknown service: {service}"}), 400

    body = request.json or {}
    url = SERVICES[service]
    if not url.endswith('/'):
        url += '/'
    url += prompt_id

    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method='PUT',
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return jsonify(json.loads(resp.read().decode()))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
