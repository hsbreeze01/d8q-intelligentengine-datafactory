# Delta Spec: Publisher Anti-Detection

## ADDED Requirements

### Requirement: Unified User-Agent in Ghost Browser

The ghost-browser launcher SHALL inject a consistent Chrome User-Agent string via `polyfill.userAgent()` plugin. The UA string MUST match the one used during the login flow (`Chrome/131.0.0.0` on Windows NT 10.0) so that the browser fingerprint is consistent between login and publishing sessions.

#### Scenario: Navigator reports non-headless UA after launch

- **Given** ghost-browser is launched with the updated launcher configuration
- **When** a page loaded in the browser queries `navigator.userAgent`
- **Then** the returned string SHALL be `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36`
- **And** the string SHALL NOT contain `HeadlessChrome`

#### Scenario: UA matches login session UA

- **Given** the login script uses `Chrome/131.0.0.0` as its User-Agent
- **And** ghost-browser launcher injects the same UA via polyfill
- **When** any request is made from the browser to the Xiaohongshu platform
- **Then** the User-Agent header SHALL be identical to the one used during login

---

### Requirement: Screen and Viewport Dimension Consistency

The ghost-browser window size and `polyfill.screen()` dimensions SHALL be identical. Mismatched values (e.g. `screen.width=1920` but viewport `1440x900`) are a strong automation signal.

#### Scenario: Screen dimensions match viewport after launch

- **Given** ghost-browser is launched with `polyfill.screen({width:1920, height:1080})`
- **And** the `--window-size` flag is set to `1920,1080`
- **When** a page queries `window.screen.width` and `window.innerWidth`
- **Then** `window.screen.width` SHALL equal `1920`
- **And** `window.screen.height` SHALL equal `1080`
- **And** the viewport dimensions SHALL be consistent with the screen dimensions

#### Scenario: Login scripts use consistent viewport

- **Given** `login_v2.py` and `login_auto.py` set viewport dimensions
- **When** these scripts open a browser session
- **Then** the viewport SHALL be `1920x1080`, matching the ghost-browser screen polyfill

---

### Requirement: Randomized Daily Schedule Offset

The scheduler SHALL apply a per-day random time offset to both `creation` and `publish` tasks so that execution times are not perfectly predictable. The offset SHALL be computed once per calendar day and cached, ensuring the same offset is used across all ticks within that day.

#### Scenario: Creation task runs within the randomized window

- **Given** a creation task has `run_at="08:30"`
- **And** the daily random offset for creation is computed once at first tick of the day
- **When** the scheduler evaluates whether to run the task
- **Then** the actual execution time SHALL fall between `08:25` and `09:10` (offset range: -5 to +40 minutes)

#### Scenario: Publish task runs after creation within randomized window

- **Given** a publish task has `run_at="08:50"`
- **And** the daily random offsets are computed together
- **When** the scheduler evaluates both tasks
- **Then** the publish offset SHALL always be greater than the creation offset (ensuring creation runs first)
- **And** the publish execution time SHALL fall between `08:45` and `09:40`

#### Scenario: Offset is stable within the same day

- **Given** the daily offset has been computed for today
- **When** the scheduler tick runs multiple times throughout the day
- **Then** the offset values SHALL remain constant (not re-randomized per tick)

#### Scenario: Offset is regenerated on a new day

- **Given** yesterday's offset was `+15` minutes for creation
- **When** the date changes to a new calendar day
- **Then** new random offsets SHALL be generated independently of the previous day's values
