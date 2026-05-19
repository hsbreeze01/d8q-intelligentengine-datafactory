# Tasks: Database Connection Safety in Standalone Modules

## 1. Connection Safety Wrapping

- [x] **1.1** Wrap `detect_heat_anomaly()` in `heat_anomaly.py` with try/finally — move `conn.close()` to `finally` block
- [x] **1.2** Wrap `_get_push_configs()` in `push_service.py` with try/finally — move `conn.close()` to `finally` block
- [x] **1.3** Wrap `send_daily_brief()` in `push_service.py` with try/finally — move `conn.close()` to `finally` block

## 2. Verification

- [x] **2.1** Run `ruff check heat_anomaly.py push_service.py` — must pass with zero errors
- [x] **2.2** Run `pytest tests/` — all existing tests must pass
