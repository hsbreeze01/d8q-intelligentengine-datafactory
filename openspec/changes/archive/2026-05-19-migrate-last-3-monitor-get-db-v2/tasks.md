# Tasks: Migrate Last 3 Monitor get_db() → get_db_ctx()

## 1. Migrate monitor API handlers

- [ ] Refactor `update_monitor_rule`, `delete_monitor_rule`, and `monitor_status` in `app.py`: wrap each function body in `with get_db_ctx() as conn:`, remove all manual `conn.close()` calls, preserve all business logic and `conn.commit()` calls exactly
- [ ] Verify: run `ruff check app.py` — zero lint errors; run `grep -n 'conn = get_db()' app.py` — zero matches; run `pytest tests/` — all pass
