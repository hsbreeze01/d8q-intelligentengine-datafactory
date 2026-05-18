# Design: Publisher Anti-Detection P0

## Overview

Three anti-detection measures to reduce the risk of Xiaohongshu identifying automated access:
1. **P0-1**: Unified User-Agent across login and publishing browser sessions
2. **P0-2**: Consistent screen/viewport dimensions
3. **P0-3**: Randomized daily schedule offset (already implemented, needs test coverage)

## Architecture Decisions

### AD-1: UA injection via ghost-browser polyfill plugin

**Decision**: Add `polyfill.userAgent()` to `launcher.mjs` plugins array, matching the exact UA string from `login_v2.py`.

**Rationale**: The ghost-browser framework supports UA polyfill as a built-in plugin. This is the least invasive way to ensure the Chromium process never leaks a HeadlessChrome or mismatched UA. Using the same string as login_v2.py ensures session continuity.

**Risk**: If Xiaohongshu updates their detection to check newer Chrome versions, the hardcoded `131.0.0.0` may become suspicious. This is acceptable for P0; version rotation can be addressed in a future change.

### AD-2: Window-size aligned with screen polyfill

**Decision**: Change `--window-size=1440,900` to `--window-size=1920,1080` in launcher.mjs, and update viewport settings in login scripts accordingly.

**Rationale**: The `polyfill.screen({width:1920, height:1080})` was already configured but the actual window was 1440x900. Any script checking `screen.width` vs `window.innerWidth` would see a clear discrepancy. Aligning both to 1920x1080 eliminates this signal.

### AD-3: Schedule offset (already implemented)

**Decision**: The random offset logic in `scheduler.py` (`_get_daily_offsets()`) is already implemented correctly. The design calls for adding test coverage to prevent regression.

**Current implementation**:
- `_get_daily_offsets()` generates offsets once per calendar day
- Creation offset: `random.randint(-5, 40)` → window 08:25~09:10
- Publish offset: `random.randint(max(creation_offset+5, -5), 50)` → ensures publish > creation
- Applied in `_tick()` via `base_time + timedelta(minutes=offset_min)`

## Cross-Project Impact

| Change | Project | Files |
|--------|---------|-------|
| P0-1 User-Agent | infopublisher | `ghost-browser/launcher.mjs` |
| P0-2 Viewport | infopublisher | `ghost-browser/launcher.mjs`, `login_v2.py`, `login_auto.py` |
| P0-3 Schedule | datafactory | `scheduler.py` (already done), `tests/test_scheduler_offset.py` (new) |

## Data Flow

### P0-1/P0-2 (infopublisher)

```
launcher.mjs startup
  → ghost browser plugins initialized
    → polyfill.userAgent("Chrome/131.0.0.0 ...")
    → polyfill.screen({width:1920, height:1080})
    → --window-size=1920,1080
  → CDP connection established
  → Xiaohongshu pages see consistent fingerprint
```

### P0-3 (datafactory)

```
scheduler _tick() [every 60s]
  → _get_daily_offsets()
    → date changed? → regenerate random offsets
    → same date? → return cached offsets
  → for each task:
    → parse run_at → compute base_time
    → apply offset → adjusted_time
    → now >= adjusted_time and not yet run today? → execute
```

## Files to Add/Modify

### infopublisher project (separate repo — manual or separate change)
- **MODIFY** `ghost-browser/launcher.mjs` — add `polyfill.userAgent()` plugin, change `--window-size`
- **MODIFY** `login_v2.py` — update viewport to 1920x1080
- **MODIFY** `login_auto.py` — update viewport to 1920x1080

### datafactory project (this repo)
- **ADD** `tests/test_scheduler_offset.py` — unit tests for `_get_daily_offsets()` and offset application logic
