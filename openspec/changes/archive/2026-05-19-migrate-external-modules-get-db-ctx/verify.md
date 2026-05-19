Verdict: PASS
Completeness: ✓ All three functions (REQ-001: detect_heat_anomaly, REQ-002: _get_push_configs, REQ-003: send_daily_brief) wrapped with try/finally as specified.
Correctness: ✓ conn.close() placed in finally block; no except clause so exceptions propagate to caller; both queries in send_daily_brief share one try/finally ensuring conn.close() fires if either fails.
Coherence: ✓ Modules remain standalone (no get_db_ctx import), all business logic/signatures/return values unchanged, pattern matches design exactly.
