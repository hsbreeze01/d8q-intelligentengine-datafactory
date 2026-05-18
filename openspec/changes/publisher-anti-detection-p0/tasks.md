# Tasks: Publisher Anti-Detection P0

## Group 1: Schedule Offset Test Coverage (datafactory — this project)

- [x] **1.1** Add `tests/test_scheduler_offset.py` — test `_get_daily_offsets()` daily regeneration, creation range [-5,+40], publish > creation invariant, same-day stability, and offset application in `_tick()` time comparison logic
- [x] **1.2** Verify scheduler module passes ruff lint and all tests (`pytest tests/test_scheduler_offset.py -v && ruff check scheduler.py`)

## Group 2: Ghost Browser Fingerprint (infopublisher project — separate change)

> These tasks modify the infopublisher project's `ghost-browser/launcher.mjs` and login scripts.
> They are listed here for traceability but MUST be executed in the infopublisher codebase.

- [x] **2.1** In `ghost-browser/launcher.mjs`: add `plugins.polyfill.userAgent({userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"})` to the plugins array, and change `--window-size=1440,900` to `--window-size=1920,1080`
- [x] **2.2** In `login_v2.py` and `login_auto.py`: update viewport/screen settings to 1920x1080 to match the launcher polyfill
- [x] **2.3** Restart `d8q-ghost-browser` and `d8q-infopublisher` services, verify `navigator.userAgent` returns Chrome/131.0.0.0 (no HeadlessChrome) and `window.screen.width === 1920` via CDP console
