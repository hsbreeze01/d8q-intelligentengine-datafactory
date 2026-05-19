Verdict: PASS
Completeness: ✓ All 6 in-scope handler categories migrated: _track_event, _init_monitor_tables, _init_events_table, _cleanup_old_events, /api/news + /api/meta, /api/proxy/tracks/* (proxy_tracks), /api/weekly/generate. Out-of-scope routes (admin, compass_pages, export_weekly) correctly left using get_db().
Correctness: ✓ get_db_ctx() correctly implemented with contextmanager decorator, row_factory, WAL pragma, and try/finally close. weekly_generate no longer leaks on early return (404 path). All try/finally/conn.close patterns replaced with with get_db_ctx(). Deprecation comment added to get_db().
Coherence: ✓ Follows existing code style. Indentation consistent. No redundant imports left behind (local `import sqlite3` in weekly_generate removed). 
Issues: none
