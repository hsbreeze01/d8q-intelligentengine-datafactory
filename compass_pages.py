"""Compass frontend pages - migrated from Compass (8087) to DataFactory (8088)

All page routes that were formerly served by Compass are now served here.
Data is fetched via compass_request() proxy to Compass API (localhost:8087).
"""
import datetime
import json
import os
import urllib.parse
import urllib.request

from flask import Blueprint, redirect, render_template, request, session

COMPASS_API = "http://localhost:8087"

compass_bp = Blueprint(
    "compass_pages",
    __name__,
    template_folder="templates/compass",
)


def _compass_request(method, path, data=None):
    """Proxy request to Compass API"""
    url = COMPASS_API + urllib.parse.quote(path, safe="/:?=&")
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    username = session.get("username", "")
    if username:
        req.add_header("X-Forwarded-User", username)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw), e.code
        except (json.JSONDecodeError, ValueError):
            return {"error": raw[:200].decode("utf-8", "replace") if isinstance(raw, bytes) else raw[:200]}, e.code
    except Exception as e:
        return {"error": str(e)}, 502


def _require_login():
    return session.get("username")


def _is_admin():
    return session.get("role") == "admin"


def _get_user_info():
    return {
        "uid": session.get("username", ""),
        "name": session.get("username", ""),
        "is_admin": _is_admin(),
    }


# ============================================================
# Compass core pages
# ============================================================


@compass_bp.route("/compass/")
def compass_index():
    if not _require_login():
        return redirect("/login")
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    code = request.args.get("code", "")
    qs = f"format=json&page={page}&page_size={page_size}"
    if code:
        qs += f"&code={code}"
    data, status = _compass_request("GET", f"/?{qs}")
    if status == 200:
        data["user"] = _get_user_info()
        return render_template("index.html", **data)
    user = _get_user_info()
    return render_template(
        "index.html", name=user["name"], stocks=[], page=1,
        total_pages=1, total_records=0, user=user,
    )


@compass_bp.route("/compass/dashboard")
def compass_dashboard():
    if not _require_login():
        return redirect("/login")
    return render_template("dashboard.html", user=_get_user_info())


@compass_bp.route("/compass/recommended/<date>")
def compass_recommended(date):
    if not _require_login():
        return redirect("/login")
    data, status = _compass_request("GET", f"/recommended/{date}?format=json")
    if status == 200:
        data["user"] = _get_user_info()
        return render_template("recommended_stocks.html", **data)
    return render_template(
        "recommended_stocks.html", recommended_stocks=[], date=date,
        prev_date="", next_date="", user=_get_user_info(),
    )


@compass_bp.route("/compass/report")
def compass_report():
    if not _require_login():
        return redirect("/login")
    return render_template("report.html", user=_get_user_info())


@compass_bp.route("/compass/policy")
def compass_policy():
    if not _require_login():
        return redirect("/login")
    return render_template("policy.html", user=_get_user_info())


# ============================================================
# Strategy pages — User view
# ============================================================


@compass_bp.route("/strategy/discover/")
def strategy_discover():
    if not _require_login():
        return redirect("/login")
    groups_data, _ = _compass_request("GET", "/api/strategy/groups/?status=active")
    subs_data, _ = _compass_request("GET", "/api/strategy/subscriptions/")
    groups = groups_data if isinstance(groups_data, list) else groups_data.get("groups", groups_data.get("items", []))
    subscriptions = subs_data if isinstance(subs_data, list) else subs_data.get("subscriptions", subs_data.get("items", []))
    sub_ids = {s.get("strategy_group_id") for s in (subscriptions or [])}
    for g in (groups or []):
        g["subscribed"] = g.get("id") in sub_ids
    stats = {
        "total_groups": len(groups or []),
        "subscribed_count": len(sub_ids),
        "open_events": 0,
    }
    return render_template(
        "strategy/discover.html",
        groups=groups or [], stats=stats,
        user=_get_user_info(), is_admin=_is_admin(),
    )


@compass_bp.route("/strategy/my/")
def strategy_my():
    if not _require_login():
        return redirect("/login")
    subs_data, _ = _compass_request("GET", "/api/strategy/subscriptions/")
    subscriptions = subs_data if isinstance(subs_data, list) else subs_data.get("subscriptions", subs_data.get("items", []))
    strategy_events = []
    for sub in (subscriptions or []):
        gid = sub.get("strategy_group_id")
        events_data, _ = _compass_request("GET", f"/api/strategy/events/?strategy_group_id={gid}&status=open")
        events = events_data if isinstance(events_data, list) else events_data.get("items", events_data.get("events", []))
        strategy_events.append({"subscription": sub, "events": events or []})
    return render_template(
        "strategy/my_strategies.html",
        strategy_events=strategy_events,
        user=_get_user_info(), is_admin=_is_admin(),
    )


@compass_bp.route("/strategy/events/<int:event_id>/")
def strategy_event_detail(event_id):
    if not _require_login():
        return redirect("/login")
    event_data, status = _compass_request("GET", f"/api/strategy/events/{event_id}/")
    if status != 200 or not event_data:
        return render_template("strategy/404.html", message="事件不存在"), 404
    event = event_data.get("event", event_data)
    created_at = event.get("created_at")
    days = 0
    if created_at:
        try:
            if isinstance(created_at, str):
                created_at = datetime.datetime.fromisoformat(created_at)
            days = (datetime.datetime.now() - created_at).days + 1
        except Exception:
            pass
    group_name = event.get("strategy_name", "")
    event["strategy_name"] = group_name
    return render_template(
        "strategy/event_detail.html",
        event=event, group_name=group_name, duration_days=days,
        user=_get_user_info(), is_admin=_is_admin(),
    )


# ============================================================
# Strategy pages — Admin view
# ============================================================


@compass_bp.route("/strategy/admin/groups/")
def strategy_admin_list():
    if not _require_login():
        return redirect("/login")
    if not _is_admin():
        return redirect("/login")
    groups_data, _ = _compass_request("GET", "/api/strategy/groups/")
    groups = groups_data if isinstance(groups_data, list) else groups_data.get("groups", groups_data.get("items", []))
    return render_template(
        "strategy/admin_list.html",
        groups=groups or [], user=_get_user_info(), is_admin=True,
    )


@compass_bp.route("/strategy/admin/groups/new")
def strategy_admin_new():
    if not _require_login():
        return redirect("/login")
    if not _is_admin():
        return redirect("/login")
    return render_template(
        "strategy/admin_edit.html",
        group=None, user=_get_user_info(), is_admin=True,
    )


@compass_bp.route("/strategy/admin/groups/<int:group_id>/edit")
def strategy_admin_edit(group_id):
    if not _require_login():
        return redirect("/login")
    if not _is_admin():
        return redirect("/login")
    group_data, status = _compass_request("GET", f"/api/strategy/groups/{group_id}/")
    group = group_data.get("group", group_data) if isinstance(group_data, dict) else group_data
    return render_template(
        "strategy/admin_edit.html",
        group=group, user=_get_user_info(), is_admin=True,
    )
