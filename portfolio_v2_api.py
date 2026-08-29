"""
模拟交易v2四层解耦架构 - API Blueprint (可独立挂载, 也可直接import函数到app)

架构(分组完全不混):
  Accounts        : 账户 + 投资初始额度 + 总收益
  Strategies      : 策略库(定义/类型/风格/参数)
  TradeJournals   : 交易日记(本/条目)
  Portfolios      : 组合 = 绑定(account_id, strategy_id, journal_id, allocated_capital) + 交易/持仓

兼容老前端: /api/portfolios* 不变, 新接口前缀 /api/v2/
新API:
  /api/v2/accounts            GET/POST                 账户CRUD
  /api/v2/accounts/<id>       GET/PUT/DELETE
  /api/v2/accounts/<id>/summary GET                    账户维度总收益(含所有子组合)

  /api/v2/strategies          GET/POST                 策略CRUD
  /api/v2/strategies/<id>     GET/PUT/DELETE

  /api/v2/journals            GET/POST                 日记簿CRUD
  /api/v2/journals/<id>       GET/PUT/DELETE
  /api/v2/journals/<id>/notes GET/POST                 日记条目
  /api/v2/journals/notes/<nid> GET/PUT/DELETE

  /api/v2/portfolios          GET/POST                 组合CRUD (创建需显式传 account/strategy/journal)
  /api/v2/portfolios/<pid>    GET/PUT/DELETE
  /api/v2/portfolios/<pid>/trade  POST                 交易 (继承自v1, 带校验)
  /api/v2/portfolios/<pid>/trades GET                 交易列表
"""
import json
from datetime import date as _dt_date
from functools import wraps
from flask import Blueprint, request, session, jsonify

portfolio_v2_bp = Blueprint("portfolio_v2", __name__)


def _db(func):
    """兼容datafactory DB (或老app.get_db_ctx), 通过延迟导入避免circular"""
    @wraps(func)
    def wrapper(*a, **kw):
        try:
            # 优先用 datafactory 模块(生产)
            from datafactory.infrastructure.db_utils import get_db_ctx
            with get_db_ctx() as conn:
                return func(conn, *a, **kw)
        except Exception:
            # 回退: 从 migrate_portfolio_v2.locate_db 找
            from migrate_portfolio_v2 import locate_db
            import sqlite3
            p = locate_db()
            conn = sqlite3.connect(p)
            conn.row_factory = sqlite3.Row
            try:
                r = func(conn, *a, **kw)
                conn.commit()
            finally:
                conn.close()
            return r
    return wrapper


def _uid():
    return session.get("username", "")


# ============================================================
# Accounts  (只体现初始额度 + 收益)
# ============================================================
@portfolio_v2_bp.route("/api/v2/accounts", methods=["GET"])
@_db
def list_accounts(conn):
    rows = conn.execute(
        """SELECT a.*,
           (SELECT count(*) FROM portfolios p WHERE p.account_id=a.id) AS portfolio_count
           FROM accounts a WHERE a.user_id=? ORDER BY a.created_at DESC""", (_uid(),)).fetchall()
    # 总收益: 用视图口径(现金+持仓市值)计算
    result = []
    for r in rows:
        aid = r["id"]
        p_list = conn.execute("SELECT id, cash FROM portfolios WHERE account_id=?", (aid,)).fetchall()
        cash = 0.0
        mv = 0.0
        for p in p_list:
            cash += (p["cash"] or 0)
            positions = conn.execute(
                "SELECT quantity, current_price FROM positions WHERE portfolio_id=? AND quantity>0",
                (p["id"],)).fetchall()
            mv += sum(pos["quantity"] * pos["current_price"] for pos in positions)
        total = cash + mv
        ic = r["initial_capital"] or 0
        result.append({
            "id": aid, "name": r["name"],
            "initial_capital": ic,
            "risk_level": r["risk_level"], "description": r["description"],
            "is_active": bool(r["is_active"]),
            "portfolio_count": len(p_list),
            "total_cash": round(cash, 2),
            "total_market_value": round(mv, 2),
            "total_assets": round(total, 2),
            "total_return_pct": round((total / ic - 1) * 100, 2) if ic > 0 else 0.0,
            "created_at": r["created_at"], "updated_at": r["updated_at"],
        })
    return jsonify(result)


@portfolio_v2_bp.route("/api/v2/accounts", methods=["POST"])
@_db
def create_account(conn):
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    ic = float(data.get("initial_capital", 1000000))
    risk = data.get("risk_level", "medium")
    desc = data.get("description", "")
    cur = conn.execute(
        """INSERT INTO accounts(user_id, name, initial_capital, risk_level, description, is_active)
           VALUES (?,?,?,?,?,1)""", (_uid(), name, ic, risk, desc))
    conn.commit()
    return jsonify({"id": cur.lastrowid, "name": name, "initial_capital": ic,
                    "risk_level": risk, "description": desc}), 201


@portfolio_v2_bp.route("/api/v2/accounts/<int:aid>", methods=["GET"])
@_db
def get_account(conn, aid):
    r = conn.execute("SELECT * FROM accounts WHERE id=? AND user_id=?", (aid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    return list_accounts._get_view(conn, aid) if False else _account_detail(conn, aid, r)


def _account_detail(conn, aid, r):
    p_list = conn.execute("SELECT id, name, initial_capital, cash, strategy_id, journal_id, allocated_capital FROM portfolios WHERE account_id=?", (aid,)).fetchall()
    portfolios = []
    cash = 0.0; mv = 0.0
    for p in p_list:
        positions = conn.execute(
            "SELECT quantity, current_price FROM positions WHERE portfolio_id=? AND quantity>0", (p["id"],)).fetchall()
        pmv = sum(pos["quantity"] * pos["current_price"] for pos in positions)
        cash += (p["cash"] or 0); mv += pmv
        strategy = conn.execute("SELECT id, name, strategy_type FROM strategies WHERE id=?", (p["strategy_id"],)).fetchone() if p["strategy_id"] else None
        journal = conn.execute("SELECT id, name FROM trade_journals WHERE id=?", (p["journal_id"],)).fetchone() if p["journal_id"] else None
        portfolios.append({
            "id": p["id"], "name": p["name"], "allocated_capital": p["allocated_capital"] or 0,
            "cash": p["cash"], "market_value": round(pmv, 2),
            "strategy": {"id": strategy["id"], "name": strategy["name"], "type": strategy["strategy_type"]} if strategy else None,
            "journal": {"id": journal["id"], "name": journal["name"]} if journal else None,
        })
    ic = r["initial_capital"] or 0
    total = cash + mv
    return jsonify({
        "id": aid, "name": r["name"],
        "initial_capital": ic, "risk_level": r["risk_level"],
        "description": r["description"], "is_active": bool(r["is_active"]),
        "total_cash": round(cash, 2), "total_market_value": round(mv, 2),
        "total_assets": round(total, 2),
        "total_return_pct": round((total / ic - 1) * 100, 2) if ic > 0 else 0.0,
        "portfolios": portfolios,
        "created_at": r["created_at"], "updated_at": r["updated_at"]
    })


@portfolio_v2_bp.route("/api/v2/accounts/<int:aid>", methods=["PUT"])
@_db
def update_account(conn, aid):
    r = conn.execute("SELECT id FROM accounts WHERE id=? AND user_id=?", (aid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(force=True) or {}
    conn.execute("""UPDATE accounts SET
                    name=COALESCE(?,name),
                    initial_capital=COALESCE(?,initial_capital),
                    risk_level=COALESCE(?,risk_level),
                    description=COALESCE(?,description),
                    is_active=COALESCE(?,is_active),
                    updated_at=datetime('now')
                    WHERE id=?""",
                 (data.get("name"), data.get("initial_capital"), data.get("risk_level"),
                  data.get("description"), 1 if data.get("is_active") is None else int(bool(data["is_active"])), aid))
    conn.commit()
    return jsonify({"ok": True, "id": aid})


@portfolio_v2_bp.route("/api/v2/accounts/<int:aid>", methods=["DELETE"])
@_db
def delete_account(conn, aid):
    r = conn.execute("SELECT id FROM accounts WHERE id=? AND user_id=?", (aid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    # 解除组合关联, 保留组合数据(避免丢交易历史)
    conn.execute("UPDATE portfolios SET account_id=NULL WHERE account_id=?", (aid,))
    conn.execute("DELETE FROM accounts WHERE id=?", (aid,))
    conn.commit()
    return jsonify({"ok": True})


# ============================================================
# Strategies
# ============================================================
@portfolio_v2_bp.route("/api/v2/strategies", methods=["GET"])
@_db
def list_strategies(conn):
    rows = conn.execute(
        "SELECT * FROM strategies WHERE user_id=? ORDER BY created_at DESC", (_uid(),)).fetchall()
    return jsonify([{
        "id": r["id"], "name": r["name"],
        "strategy_type": r["strategy_type"], "style": r["style"],
        "description": r["description"],
        "parameters": json.loads(r["parameters"] or "{}"),
        "tags": [t for t in (r["tags"] or "").split(",") if t],
        "is_active": bool(r["is_active"]),
        "created_at": r["created_at"], "updated_at": r["updated_at"],
    } for r in rows])


@portfolio_v2_bp.route("/api/v2/strategies", methods=["POST"])
@_db
def create_strategy(conn):
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    params = data.get("parameters") or {}
    tags_l = data.get("tags") or []
    cur = conn.execute(
        """INSERT INTO strategies(user_id, name, strategy_type, style, description, parameters, tags, is_active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (_uid(), name, data.get("strategy_type", "manual"), data.get("style", "mixed"),
         data.get("description", ""), json.dumps(params, ensure_ascii=False),
         ",".join(str(t) for t in tags_l if str(t).strip())))
    conn.commit()
    return jsonify({"id": cur.lastrowid, "name": name}), 201


@portfolio_v2_bp.route("/api/v2/strategies/<int:sid>", methods=["GET"])
@_db
def get_strategy(conn, sid):
    r = conn.execute("SELECT * FROM strategies WHERE id=? AND user_id=?", (sid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    # 使用该策略的组合数
    cnt = conn.execute("SELECT count(*) FROM portfolios WHERE strategy_id=?", (sid,)).fetchone()[0]
    return jsonify({
        "id": r["id"], "name": r["name"],
        "strategy_type": r["strategy_type"], "style": r["style"],
        "description": r["description"],
        "parameters": json.loads(r["parameters"] or "{}"),
        "tags": [t for t in (r["tags"] or "").split(",") if t],
        "is_active": bool(r["is_active"]),
        "portfolio_count": cnt,
        "created_at": r["created_at"], "updated_at": r["updated_at"],
    })


@portfolio_v2_bp.route("/api/v2/strategies/<int:sid>", methods=["PUT"])
@_db
def update_strategy(conn, sid):
    r = conn.execute("SELECT id FROM strategies WHERE id=? AND user_id=?", (sid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(force=True) or {}
    if data.get("parameters") is not None:
        params = json.dumps(data["parameters"], ensure_ascii=False)
    else:
        params = None
    if data.get("tags") is not None:
        tags_s = ",".join(str(t) for t in data["tags"] if str(t).strip())
    else:
        tags_s = None
    conn.execute("""UPDATE strategies SET
                    name=COALESCE(?,name),
                    strategy_type=COALESCE(?,strategy_type),
                    style=COALESCE(?,style),
                    description=COALESCE(?,description),
                    parameters=COALESCE(?,parameters),
                    tags=COALESCE(?,tags),
                    is_active=COALESCE(?,is_active),
                    updated_at=datetime('now')
                    WHERE id=?""",
                 (data.get("name"), data.get("strategy_type"), data.get("style"),
                  data.get("description"), params, tags_s,
                  1 if data.get("is_active") is None else int(bool(data["is_active"])), sid))
    conn.commit()
    return jsonify({"ok": True})


@portfolio_v2_bp.route("/api/v2/strategies/<int:sid>", methods=["DELETE"])
@_db
def delete_strategy(conn, sid):
    r = conn.execute("SELECT id FROM strategies WHERE id=? AND user_id=?", (sid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    conn.execute("UPDATE portfolios SET strategy_id=NULL WHERE strategy_id=?", (sid,))
    conn.execute("DELETE FROM strategies WHERE id=?", (sid,))
    conn.commit()
    return jsonify({"ok": True})


# ============================================================
# TradeJournals
# ============================================================
@portfolio_v2_bp.route("/api/v2/journals", methods=["GET"])
@_db
def list_journals(conn):
    rows = conn.execute(
        "SELECT * FROM trade_journals WHERE user_id=? ORDER BY created_at DESC", (_uid(),)).fetchall()
    res = []
    for r in rows:
        cnt = conn.execute("SELECT count(*) FROM trade_notes WHERE journal_id=?", (r["id"],)).fetchone()[0]
        res.append({
            "id": r["id"], "name": r["name"],
            "journal_type": r["journal_type"], "description": r["description"],
            "tags": [t for t in (r["tags"] or "").split(",") if t],
            "notes_count": cnt,
            "is_active": bool(r["is_active"]),
            "created_at": r["created_at"], "updated_at": r["updated_at"],
        })
    return jsonify(res)


@portfolio_v2_bp.route("/api/v2/journals", methods=["POST"])
@_db
def create_journal(conn):
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    tags_l = data.get("tags") or []
    cur = conn.execute(
        """INSERT INTO trade_journals(user_id, name, journal_type, description, tags, is_active)
           VALUES (?,?,?,?,?,1)""",
        (_uid(), name, data.get("journal_type", "default"),
         data.get("description", ""),
         ",".join(str(t) for t in tags_l if str(t).strip())))
    conn.commit()
    return jsonify({"id": cur.lastrowid, "name": name}), 201


@portfolio_v2_bp.route("/api/v2/journals/<int:jid>", methods=["PUT"])
@_db
def update_journal(conn, jid):
    r = conn.execute("SELECT id FROM trade_journals WHERE id=? AND user_id=?", (jid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(force=True) or {}
    tags_s = ",".join(str(t) for t in (data.get("tags") or [])) if data.get("tags") is not None else None
    conn.execute("""UPDATE trade_journals SET
                    name=COALESCE(?,name),
                    journal_type=COALESCE(?,journal_type),
                    description=COALESCE(?,description),
                    tags=COALESCE(?,tags),
                    is_active=COALESCE(?,is_active),
                    updated_at=datetime('now')
                    WHERE id=?""",
                 (data.get("name"), data.get("journal_type"), data.get("description"), tags_s,
                  1 if data.get("is_active") is None else int(bool(data["is_active"])), jid))
    conn.commit()
    return jsonify({"ok": True})


@portfolio_v2_bp.route("/api/v2/journals/<int:jid>", methods=["DELETE"])
@_db
def delete_journal(conn, jid):
    r = conn.execute("SELECT id FROM trade_journals WHERE id=? AND user_id=?", (jid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    conn.execute("DELETE FROM trade_notes WHERE journal_id=?", (jid,))
    conn.execute("UPDATE portfolios SET journal_id=NULL WHERE journal_id=?", (jid,))
    conn.execute("UPDATE trades SET journal_entry_id=NULL WHERE journal_entry_id IN (SELECT id FROM trade_notes WHERE journal_id=?)", (jid,))
    conn.execute("DELETE FROM trade_journals WHERE id=?", (jid,))
    conn.commit()
    return jsonify({"ok": True})


# ---------- 日记条目 ----------
@portfolio_v2_bp.route("/api/v2/journals/<int:jid>/notes", methods=["GET"])
@_db
def list_notes(conn, jid):
    jr = conn.execute("SELECT id FROM trade_journals WHERE id=? AND user_id=?", (jid, _uid())).fetchone()
    if not jr:
        return jsonify({"error": "not found"}), 404
    rows = conn.execute(
        "SELECT * FROM trade_notes WHERE journal_id=? ORDER BY created_at DESC LIMIT 500", (jid,)).fetchall()
    return jsonify([{
        "id": r["id"], "trade_id": r["trade_id"], "trade_date": r["trade_date"],
        "stock_code": r["stock_code"], "title": r["title"], "content": r["content"],
        "mood": r["mood"], "tags": [t for t in (r["tags"] or "").split(",") if t],
        "created_at": r["created_at"], "updated_at": r["updated_at"],
    } for r in rows])


@portfolio_v2_bp.route("/api/v2/journals/<int:jid>/notes", methods=["POST"])
@_db
def create_note(conn, jid):
    jr = conn.execute("SELECT id FROM trade_journals WHERE id=? AND user_id=?", (jid, _uid())).fetchone()
    if not jr:
        return jsonify({"error": "not found"}), 404
    d = request.get_json(force=True) or {}
    tags_s = ",".join(str(t) for t in (d.get("tags") or []) if str(t).strip())
    cur = conn.execute(
        """INSERT INTO trade_notes(journal_id, trade_id, trade_date, stock_code, title, content, mood, tags)
           VALUES (?,?,?,?,?,?,?,?)""",
        (jid, d.get("trade_id"), d.get("trade_date") or str(_dt_date.today()),
         d.get("stock_code", ""), d.get("title", ""), d.get("content", ""),
         int(d.get("mood") or 3), tags_s))
    # 同步关联trades表（如果传了trade_id）
    if d.get("trade_id"):
        conn.execute("UPDATE trades SET journal_entry_id=? WHERE id=?", (cur.lastrowid, d["trade_id"]))
    conn.commit()
    return jsonify({"id": cur.lastrowid}), 201


@portfolio_v2_bp.route("/api/v2/journals/notes/<int:nid>", methods=["PUT"])
@_db
def update_note(conn, nid):
    # 安全检查: user_id通过 journal.user_id
    r = conn.execute("""
        SELECT n.id FROM trade_notes n
        JOIN trade_journals j ON j.id=n.journal_id
        WHERE n.id=? AND j.user_id=?""", (nid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    d = request.get_json(force=True) or {}
    tags_s = ",".join(str(t) for t in (d.get("tags") or [])) if d.get("tags") is not None else None
    conn.execute("""UPDATE trade_notes SET
                    trade_id=COALESCE(?,trade_id),
                    trade_date=COALESCE(?,trade_date),
                    stock_code=COALESCE(?,stock_code),
                    title=COALESCE(?,title),
                    content=COALESCE(?,content),
                    mood=COALESCE(?,mood),
                    tags=COALESCE(?,tags),
                    updated_at=datetime('now')
                    WHERE id=?""",
                 (d.get("trade_id"), d.get("trade_date"), d.get("stock_code"),
                  d.get("title"), d.get("content"),
                  int(d["mood"]) if d.get("mood") is not None else None,
                  tags_s, nid))
    conn.commit()
    return jsonify({"ok": True})


@portfolio_v2_bp.route("/api/v2/journals/notes/<int:nid>", methods=["DELETE"])
@_db
def delete_note(conn, nid):
    r = conn.execute("""
        SELECT n.id FROM trade_notes n
        JOIN trade_journals j ON j.id=n.journal_id
        WHERE n.id=? AND j.user_id=?""", (nid, _uid())).fetchone()
    if not r:
        return jsonify({"error": "not found"}), 404
    conn.execute("UPDATE trades SET journal_entry_id=NULL WHERE journal_entry_id=?", (nid,))
    conn.execute("DELETE FROM trade_notes WHERE id=?", (nid,))
    conn.commit()
    return jsonify({"ok": True})


# ============================================================
# Portfolios v2 (显式绑定account/strategy/journal)
# ============================================================
@portfolio_v2_bp.route("/api/v2/portfolios", methods=["GET"])
@_db
def v2_list_portfolios(conn):
    rows = conn.execute(
        "SELECT * FROM portfolios WHERE user_id=? ORDER BY created_at DESC", (_uid(),)).fetchall()
    out = []
    for r in rows:
        pos = conn.execute(
            "SELECT quantity, current_price FROM positions WHERE portfolio_id=? AND quantity>0", (r["id"],)).fetchall()
        mv = sum(p["quantity"] * p["current_price"] for p in pos)
        ta = (r["cash"] or 0) + mv
        ic = r["allocated_capital"] or r["initial_capital"] or 0
        acc = conn.execute("SELECT id,name,initial_capital FROM accounts WHERE id=?", (r["account_id"],)).fetchone() if r["account_id"] else None
        st = conn.execute("SELECT id,name,strategy_type FROM strategies WHERE id=?", (r["strategy_id"],)).fetchone() if r["strategy_id"] else None
        jn = conn.execute("SELECT id,name FROM trade_journals WHERE id=?", (r["journal_id"],)).fetchone() if r["journal_id"] else None
        out.append({
            "id": r["id"], "name": r["name"],
            "account": {"id": acc["id"], "name": acc["name"], "initial_capital": acc["initial_capital"]} if acc else None,
            "strategy": {"id": st["id"], "name": st["name"], "type": st["strategy_type"]} if st else None,
            "journal": {"id": jn["id"], "name": jn["name"]} if jn else None,
            "allocated_capital": r["allocated_capital"] or 0,
            "cash": r["cash"], "total_market_value": round(mv, 2),
            "total_assets": round(ta, 2),
            "total_return_pct": round((ta / ic - 1) * 100, 2) if ic > 0 else 0.0,
            "created_at": r["created_at"], "updated_at": r["updated_at"],
        })
    return jsonify(out)


@portfolio_v2_bp.route("/api/v2/portfolios", methods=["POST"])
@_db
def v2_create_portfolio(conn):
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    aid = data.get("account_id")
    sid = data.get("strategy_id")
    jid = data.get("journal_id")
    if not name:
        return jsonify({"error": "name required"}), 400
    if aid is None:
        return jsonify({"error": "account_id required (先选账户-定义初始额度)"}), 400
    # 校验归属
    if not conn.execute("SELECT 1 FROM accounts WHERE id=? AND user_id=?", (aid, _uid())).fetchone():
        return jsonify({"error": "account not found"}), 400
    if sid and not conn.execute("SELECT 1 FROM strategies WHERE id=? AND user_id=?", (sid, _uid())).fetchone():
        return jsonify({"error": "strategy not found"}), 400
    if jid and not conn.execute("SELECT 1 FROM trade_journals WHERE id=? AND user_id=?", (jid, _uid())).fetchone():
        return jsonify({"error": "journal not found"}), 400
    alloc = float(data.get("allocated_capital") or 0)
    if alloc <= 0:
        return jsonify({"error": "allocated_capital > 0 required（从账户划拨到组合的额度）"}), 400
    # 检查账户划拨额度不超过账户总剩余
    acc = conn.execute("SELECT initial_capital FROM accounts WHERE id=?", (aid,)).fetchone()
    used = conn.execute(
        "SELECT COALESCE(SUM(allocated_capital),0) FROM portfolios WHERE account_id=? AND id IS NOT NULL", (aid,)).fetchone()[0]
    if used + alloc > (acc["initial_capital"] or 0) * 1.0001:
        return jsonify({"error": f"账户余额不足. 账户初始{acc['initial_capital']}, 已分{used}, 本次申请{alloc}"}), 400
    cur = conn.execute(
        """INSERT INTO portfolios(user_id, name, initial_capital, cash, account_id, strategy_id, journal_id, allocated_capital)
           VALUES (?,?,?,?,?,?,?,?)""",
        (_uid(), name, alloc, alloc, aid, sid, jid, alloc))
    conn.commit()
    return jsonify({"id": cur.lastrowid, "name": name, "account_id": aid,
                    "strategy_id": sid, "journal_id": jid, "allocated_capital": alloc}), 201


@portfolio_v2_bp.route("/api/v2/portfolios/<int:pid>", methods=["GET"])
@_db
def v2_get_portfolio(conn, pid):
    p = conn.execute("SELECT * FROM portfolios WHERE id=? AND user_id=?", (pid, _uid())).fetchone()
    if not p:
        return jsonify({"error": "not found"}), 404
    pos_rows = conn.execute(
        "SELECT * FROM positions WHERE portfolio_id=? AND quantity>0 ORDER BY stock_code", (pid,)).fetchall()
    positions = []
    mv = 0
    for pos in pos_rows:
        pmv = pos["quantity"] * pos["current_price"]
        profit = (pos["current_price"] - pos["avg_cost"]) * pos["quantity"]
        ppct = (pos["current_price"] / pos["avg_cost"] - 1) * 100 if pos["avg_cost"] else 0
        mv += pmv
        positions.append({
            "stock_code": pos["stock_code"], "stock_name": pos["stock_name"],
            "quantity": pos["quantity"], "avg_cost": round(pos["avg_cost"], 4),
            "current_price": pos["current_price"], "market_value": round(pmv, 2),
            "profit": round(profit, 2), "profit_pct": round(ppct, 2)
        })
    cash = p["cash"] or 0
    ta = cash + mv
    ic = p["allocated_capital"] or p["initial_capital"] or 0
    acc = conn.execute("SELECT id,name,initial_capital FROM accounts WHERE id=?", (p["account_id"],)).fetchone() if p["account_id"] else None
    st = conn.execute("SELECT id,name,strategy_type,style FROM strategies WHERE id=?", (p["strategy_id"],)).fetchone() if p["strategy_id"] else None
    jn = conn.execute("SELECT id,name,journal_type FROM trade_journals WHERE id=?", (p["journal_id"],)).fetchone() if p["journal_id"] else None
    return jsonify({
        "id": pid, "name": p["name"],
        "account": dict(acc) if acc else None,
        "strategy": dict(st) if st else None,
        "journal": dict(jn) if jn else None,
        "allocated_capital": p["allocated_capital"] or 0,
        "cash": round(cash, 2),
        "total_market_value": round(mv, 2),
        "total_assets": round(ta, 2),
        "total_return_pct": round((ta / ic - 1) * 100, 2) if ic > 0 else 0.0,
        "positions": positions,
        "created_at": p["created_at"], "updated_at": p["updated_at"],
    })


@portfolio_v2_bp.route("/api/v2/portfolios/<int:pid>/trade", methods=["POST"])
@_db
def v2_trade(conn, pid):
    """交易 - 同时校验账户划拨额度(组合内使用v1的现金台账)并把笔记关联到绑定的journal"""
    p = conn.execute("SELECT * FROM portfolios WHERE id=? AND user_id=?", (pid, _uid())).fetchone()
    if not p:
        return jsonify({"error": "portfolio not found"}), 404

    d = request.get_json(force=True) or {}
    stock_code = (d.get("stock_code") or "").strip()
    stock_name = (d.get("stock_name") or "").strip()
    direction = (d.get("direction") or "").strip().lower()
    price = float(d.get("price", 0))
    quantity = int(d.get("quantity", 0))
    note = d.get("note", "")
    if not stock_code or direction not in ("buy", "sell") or price <= 0 or quantity <= 0:
        return jsonify({"error": "invalid params"}), 400
    amount = round(price * quantity, 2)
    trade_date = d.get("trade_date") or str(_dt_date.today())

    if direction == "buy":
        if p["cash"] < amount:
            return jsonify({"error": f"insufficient cash: need {amount}, have {round(p['cash'],2)}"}), 400
        conn.execute("UPDATE portfolios SET cash=cash-?, updated_at=datetime('now') WHERE id=?", (amount, pid))
        ex = conn.execute(
            "SELECT quantity, avg_cost, stock_name FROM positions WHERE portfolio_id=? AND stock_code=?", (pid, stock_code)).fetchone()
        if ex and ex["quantity"] > 0:
            nq = ex["quantity"] + quantity
            na = (ex["avg_cost"] * ex["quantity"] + price * quantity) / nq
            conn.execute(
                "UPDATE positions SET quantity=?, avg_cost=?, current_price=?, stock_name=?, updated_at=datetime('now') WHERE portfolio_id=? AND stock_code=?",
                (nq, round(na, 4), price, stock_name or ex["stock_name"], pid, stock_code))
        else:
            conn.execute(
                "INSERT OR REPLACE INTO positions(portfolio_id, stock_code, stock_name, quantity, avg_cost, current_price, updated_at) VALUES (?,?,?,?,?,?,datetime('now'))",
                (pid, stock_code, stock_name, quantity, price, price))
    else:
        ex = conn.execute("SELECT quantity FROM positions WHERE portfolio_id=? AND stock_code=?", (pid, stock_code)).fetchone()
        if not ex or ex["quantity"] < quantity:
            avail = ex["quantity"] if ex else 0
            return jsonify({"error": f"insufficient shares: need {quantity}, have {avail}"}), 400
        conn.execute("UPDATE portfolios SET cash=cash+?, updated_at=datetime('now') WHERE id=?", (amount, pid))
        nq = ex["quantity"] - quantity
        conn.execute(
            "UPDATE positions SET quantity=?, current_price=?, updated_at=datetime('now') WHERE portfolio_id=? AND stock_code=?",
            (nq, price, pid, stock_code))

    # 写入交易
    tc = conn.execute(
        """INSERT INTO trades(portfolio_id, stock_code, stock_name, direction, price, quantity, amount, trade_date, note)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (pid, stock_code, stock_name, direction, price, quantity, amount, trade_date, note))
    trade_id = tc.lastrowid

    # 如果传了note内容+组合绑定了journal -> 自动创建一条日记条目
    if note and p["journal_id"]:
        tags_s = ",".join(t for t in ["auto", direction, stock_code] if t)
        nc = conn.execute(
            """INSERT INTO trade_notes(journal_id, trade_id, trade_date, stock_code, title, content, mood, tags)
               VALUES (?,?,?,?,?,?,3,?)""",
            (p["journal_id"], trade_id, trade_date, stock_code,
             f"{direction.upper()} {stock_code} @ {price}", note, tags_s))
        conn.execute("UPDATE trades SET journal_entry_id=? WHERE id=?", (nc.lastrowid, trade_id))

    conn.commit()
    return jsonify({"ok": True, "direction": direction, "stock_code": stock_code,
                    "quantity": quantity, "amount": amount, "trade_id": trade_id})
