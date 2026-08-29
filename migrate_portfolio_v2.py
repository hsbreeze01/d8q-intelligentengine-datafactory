"""
模拟交易架构v2迁移脚本 (可重复执行, 幂等, 保留历史数据)

原架构: 一个 portfolios 表 混装(用户/初始资金/名字/现金/交易)
新架构 (4层解耦, 自由组合, 账户-策略-日记-组合 分组不混):
┌─────────────────────────────────────────────────────────────┐
│  Accounts        : 账户（仅体现初始额度 + 交易收益归属）      │
│  Strategies      : 策略定义（选股利器/择时/风格/调仓频率）    │
│  TradeJournals   : 交易日记（独立的交易笔记容器）             │
│  Portfolios      : 组合 = 绑定(account_id + strategy_id +    │
│                    journal_id + 初始额度切分 + 实际交易持仓)  │
└─────────────────────────────────────────────────────────────┘

迁移步骤:
1. 创建 accounts / strategies / trade_journals 三张新表
2. 给老 portfolios 增加 account_id / strategy_id / journal_id 外键
3. 为老数据自动生成同名 account + 默认策略 + 专属日记, 保证兼容
4. 创建 trades -> journal_id 外键，支持每笔交易写笔记
5. 记录迁移版本号，重复执行安全跳过
"""
import os, sys, json, sqlite3
from datetime import datetime

DB_FALLBACK_CANDIDATES = [
    os.environ.get("DB_PATH", ""),
    # datafactory默认路径(如在src里引用)
    "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "warehouse.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "factory.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "financial_news.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "app.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db"),
    # 尝试通过 PYTHONPATH 找到 datafactory 模块获取 DB_PATH
    "",
]

def locate_db():
    # 优先从 datafactory.infrastructure.db_utils 取(如果环境有PYTHONPATH)
    for extra in ["src", "."]:
        sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), extra)
        if sp not in sys.path and os.path.isdir(sp):
            sys.path.insert(0, sp)
    try:
        from datafactory.infrastructure.db_utils import DB_PATH as _dp
        if _dp and os.path.exists(_dp):
            return _dp
    except Exception:
        pass
    for p in DB_FALLBACK_CANDIDATES:
        if p and os.path.exists(p):
            # 验证portfolios表存在
            try:
                c = sqlite3.connect(p)
                has = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='portfolios'").fetchone()[0]
                c.close()
                if has:
                    return p
            except Exception:
                continue
    return None

def col_exists(conn, table, col):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == col for r in rows)

def table_exists(conn, name):
    return conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()[0] > 0

SCHEMA_VERSION = "2.0.0"

def run_migrate(db_path=None):
    db = db_path or locate_db()
    assert db, ("找不到包含 portfolios 表的 SQLite DB。"
                f"\n候选路径: {[c for c in DB_FALLBACK_CANDIDATES if c]}"
                "\n请设置 DB_PATH 环境变量。")
    print(f"[migrate] DB = {db}")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 创建 schema_migrations 表做幂等版本记录
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at DATETIME,
            description TEXT
        )
    """)

    def applied(v):
        return cur.execute("SELECT 1 FROM schema_migrations WHERE version=?", (v,)).fetchone() is not None

    def mark(v, desc):
        cur.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?,?,?)",
                    (v, datetime.now().isoformat(), desc))

    # ---------- 1. Accounts 账户(只体现初始额度 + 交易收益归属) ----------
    if not applied("2.0.1-accounts"):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                initial_capital REAL NOT NULL DEFAULT 1000000,  -- 投资初始额度
                risk_level TEXT DEFAULT 'medium',                -- low/medium/high
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);
        """)
        mark("2.0.1-accounts", "新建账户表 accounts — 仅承载初始额度与收益归属")
        print("  ✓ 2.0.1 accounts")
    else:
        print("  ⏭ 2.0.1 accounts (已应用)")

    # ---------- 2. Strategies 策略库 ----------
    if not applied("2.0.2-strategies"):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                strategy_type TEXT DEFAULT 'manual',   -- manual/cta/value/growth/arbitrage/event_driven
                style TEXT DEFAULT 'mixed',            -- 短线/中线/长线/波段/打板/动量/反转
                description TEXT DEFAULT '',           -- 策略说明
                parameters TEXT DEFAULT '{}',          -- JSON: 止损/止盈/仓位上限/选股条件等
                tags TEXT DEFAULT '',                   -- 逗号分隔
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_strategies_user ON strategies(user_id);
            CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);
        """)
        mark("2.0.2-strategies", "新建策略库 strategies — 策略定义独立于账户和组合")
        print("  ✓ 2.0.2 strategies")
    else:
        print("  ⏭ 2.0.2 strategies (已应用)")

    # ---------- 3. TradeJournals 交易日记(独立的笔记容器) ----------
    if not applied("2.0.3-journals"):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trade_journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                journal_type TEXT DEFAULT 'default',    -- default/intraday/daily_report/error_review
                description TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS trade_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_id INTEGER NOT NULL,
                trade_id INTEGER,                       -- 可关联某笔交易
                trade_date TEXT,
                stock_code TEXT,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',                -- 决策思路、盘后复盘、错误教训
                mood INTEGER DEFAULT 3,                 -- 1-5 情绪冷静度
                tags TEXT DEFAULT '',
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_journals_user ON trade_journals(user_id);
            CREATE INDEX IF NOT EXISTS idx_notes_journal ON trade_notes(journal_id);
            CREATE INDEX IF NOT EXISTS idx_notes_trade ON trade_notes(trade_id);
            CREATE INDEX IF NOT EXISTS idx_notes_date ON trade_notes(trade_date);
        """)
        mark("2.0.3-journals", "新建交易日记 trade_journals + 日记条目 trade_notes")
        print("  ✓ 2.0.3 trade_journals")
    else:
        print("  ⏭ 2.0.3 trade_journals (已应用)")

    # ---------- 4. portfolios 加3个外键 + 资金切分字段 ----------
    cols_to_add = [
        ("account_id",  "INTEGER REFERENCES accounts(id)"),
        ("strategy_id", "INTEGER REFERENCES strategies(id)"),
        ("journal_id",  "INTEGER REFERENCES trade_journals(id)"),
        ("allocated_capital", "REAL DEFAULT 0 -- 从账户划拨到本组合的额度,<=账户.initial_capital"),
    ]
    migrated = False
    for cname, cdef in cols_to_add:
        if not col_exists(conn, "portfolios", cname):
            cur.execute(f"ALTER TABLE portfolios ADD COLUMN {cname} {cdef}")
            print(f"  ✓ portfolios +{cname}")
            migrated = True
    if not migrated:
        print("  ⏭ portfolios 外键已就绪")

    # trades 增加 journal_entry_id (关联日记条目)
    if not col_exists(conn, "trades", "journal_entry_id"):
        cur.execute("ALTER TABLE trades ADD COLUMN journal_entry_id INTEGER REFERENCES trade_notes(id)")
        print("  ✓ trades +journal_entry_id")
    else:
        print("  ⏭ trades +journal_entry_id 已就绪")

    # ---------- 5. 历史数据补全: 老 portfolios -> 生成同名 account/strategy/journal ----------
    if not applied("2.0.5-backfill"):
        # 为每个用户建立 默认策略 + 默认日记 复用
        # 先找到所有已有 portfolios (含user_id且没填account_id)
        old_rows = cur.execute("""
            SELECT id, user_id, name, initial_capital FROM portfolios
            WHERE (account_id IS NULL OR account_id = 0)
        """).fetchall()

        stats = {"portfolios": 0, "accounts": 0, "strategies": 0, "journals": 0}
        cache = {}  # (user_id, kind) -> id

        def get_or_create(user_id, kind):
            """kind in ('account_admin_default', 'strategy_default', 'journal_default',
                        'account_portfolio_XXX')"""
            if (user_id, kind) in cache:
                return cache[(user_id, kind)]

            if kind.startswith("account_portfolio_"):
                # 按组合名创建账户
                pname = kind[len("account_portfolio_"):]
                cur.execute("""
                    INSERT INTO accounts(user_id, name, initial_capital, description, risk_level, is_active)
                    VALUES (?,?,?,?, 'medium', 1)
                """, (user_id, pname + "账户", None, f"由旧组合[{pname}]迁移自动生成, 已预拨100%额度进对应组合"))
                # initial_capital稍后单独update
                aid = cur.lastrowid
                cache[(user_id, kind)] = aid
                stats["accounts"] += 1
                return aid

            if kind == "strategy_default":
                cur.execute("""
                    INSERT INTO strategies(user_id, name, strategy_type, style, description, parameters, tags, is_active)
                    VALUES (?,?, 'manual','mixed',?, '{}', '默认', 1)
                """, (user_id, f"{user_id}-默认策略", "系统默认策略(手动交易), 可随时替换"))
                sid = cur.lastrowid
                cache[(user_id, kind)] = sid
                stats["strategies"] += 1
                return sid

            if kind == "journal_default":
                cur.execute("""
                    INSERT INTO trade_journals(user_id, name, journal_type, description, tags, is_active)
                    VALUES (?,?, 'default',?, '默认', 1)
                """, (user_id, f"{user_id}-交易日记", f"{user_id} 默认交易日记, 可在组合中自由绑定"))
                jid = cur.lastrowid
                cache[(user_id, kind)] = jid
                stats["journals"] += 1
                return jid

        for r in old_rows:
            pid, uid, pname, initial = r["id"], r["user_id"], r["name"], r["initial_capital"] or 1000000
            aid = get_or_create(uid, f"account_portfolio_{pname}")
            # update account初始资金
            cur.execute("UPDATE accounts SET initial_capital=? WHERE id=?", (initial, aid))
            sid = get_or_create(uid, "strategy_default")
            jid = get_or_create(uid, "journal_default")
            # 写回portfolios外键, 并且allocated_capital=100% (旧组合直接继承账户的全部初始资金)
            cur.execute("""
                UPDATE portfolios
                SET account_id=?, strategy_id=?, journal_id=?, allocated_capital=?
                WHERE id=?
            """, (aid, sid, jid, initial, pid))
            stats["portfolios"] += 1

        print(f"  ✓ 2.0.5 backfill: 迁移{stats['portfolios']}个组合 + {stats['accounts']}账户 + {stats['strategies']}策略 + {stats['journals']}日记")
        mark("2.0.5-backfill", f"历史数据回填: 组合{stats['portfolios']}/账户{stats['accounts']}/策略{stats['strategies']}/日记{stats['journals']}")
    else:
        print("  ⏭ 2.0.5 backfill (已应用)")

    # ---------- 6. 为新架构建view: 方便老前端继续用 ----------
    if not applied("2.0.6-views"):
        cur.executescript("""
            CREATE VIEW IF NOT EXISTS v_account_summary AS
            SELECT
                a.id, a.user_id, a.name, a.initial_capital, a.risk_level, a.description, a.is_active,
                COUNT(DISTINCT p.id) AS portfolio_count,
                COALESCE(SUM(p.cash), 0) AS total_cash,
                COALESCE(SUM((SELECT COALESCE(SUM(quantity*current_price),0)
                              FROM positions WHERE portfolio_id=p.id AND quantity>0)),0) AS total_market_value,
                COALESCE(SUM(p.cash),0)
                  + COALESCE(SUM((SELECT COALESCE(SUM(quantity*current_price),0)
                                  FROM positions WHERE portfolio_id=p.id AND quantity>0)),0) AS total_assets,
                CASE WHEN a.initial_capital>0
                     THEN ROUND(100.0*(
                        COALESCE(SUM(p.cash),0)
                        + COALESCE(SUM((SELECT COALESCE(SUM(quantity*current_price),0)
                                        FROM positions WHERE portfolio_id=p.id AND quantity>0)),0)
                        - a.initial_capital)/a.initial_capital, 2)
                     ELSE 0 END AS total_return_pct,
                a.created_at, a.updated_at
            FROM accounts a
            LEFT JOIN portfolios p ON p.account_id=a.id
            GROUP BY a.id;
        """)
        mark("2.0.6-views", "账户总览视图 v_account_summary")
        print("  ✓ 2.0.6 views (v_account_summary)")
    else:
        print("  ⏭ 2.0.6 views (已应用)")

    mark(SCHEMA_VERSION, "portfolio v2 四层解耦架构迁移完成")
    conn.commit()

    # ---------- 验证 ----------
    print("\n[migrate] 验证:")
    for t in ["accounts", "strategies", "trade_journals", "trade_notes",
              "portfolios", "positions", "trades", "net_value_history",
              "v_account_summary"]:
        try:
            n = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  {t:22s}: {n} 条")
        except Exception as e:
            print(f"  {t:22s}: 不存在 ({e})")

    conn.close()
    print("\n✓ Portfolio v2 迁移完成 (幂等, 可重复执行)")
    return db

if __name__ == "__main__":
    run_migrate(sys.argv[1] if len(sys.argv) > 1 else None)
