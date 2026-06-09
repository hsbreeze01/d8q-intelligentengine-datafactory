# Spec: Monitor Rules Initialization Fix

## MODIFIED Requirements

### Requirement: builtin monitor rules always populated

The `_init_monitor_tables()` function SHALL reliably insert 4 builtin monitor rules
into the `monitor_rules` table on every application startup where the table has zero
builtin rows. The initialization error handler at module level MUST log the exception
instead of silently swallowing it (`except Exception: pass` → `except Exception as e: logger.error(...)`).

#### Scenario: 4 builtin rules inserted on fresh database

- **testable**: true
- **target**: app.py::_init_monitor_tables
- **Given** a fresh SQLite database with monitor_rules table created but 0 builtin rows
- **When** `_init_monitor_tables()` is called
- **Then** exactly 4 rows with builtin=1 SHALL exist: "小红书 Cookie 有效性", "Ghost Browser CDP 连通性", "发布锁状态", "发布服务健康"

#### Scenario: builtin rules are idempotent across multiple calls

- **testable**: true
- **target**: app.py::_init_monitor_tables
- **Given** a SQLite database where 4 builtin monitor rules already exist
- **When** `_init_monitor_tables()` is called again
- **Then** the builtin rule count SHALL remain 4 (no duplicates)

---

### Requirement: monitor rules config_json driven by infra_assets

The builtin monitor rules' `config_json` values SHALL be constructed by querying
host/port from the `infra_assets` table rather than using hardcoded `PUBLISHER_API`
or literal IP addresses. This applies specifically to:

- "小红书 Cookie 有效性" rule: url and status_url MUST be built from infra_assets `infopublisher` row
- "发布服务健康" rule: url MUST be built from infra_assets `infopublisher` row
- "Ghost Browser CDP 连通性" rule: url MUST be built from infra_assets `ghost_browser` row (using 49.234.48.221:9222, NOT localhost:9222)

The `_init_monitor_tables()` function MUST call `_init_infra_assets()` first (or rely
on it having been called already) so that infra_assets data is available for URL construction.

#### Scenario: monitor rules config_json contains no hardcoded PUBLISHER_API literal

- **testable**: true
- **target**: app.py::_init_monitor_tables
- **Given** a fresh SQLite database where both _init_infra_assets() and _init_monitor_tables() have been called
- **When** the config_json of builtin rules is inspected
- **Then** no config_json value SHALL contain the string literal "PUBLISHER_API" or variable interpolation artifacts like "http://$PUBLISHER_API"

#### Scenario: CDP rule uses direct remote address not localhost tunnel

- **testable**: true
- **target**: app.py::_init_monitor_tables
- **Given** a fresh SQLite database where both _init_infra_assets() and _init_monitor_tables() have been called
- **When** the config_json of the "Ghost Browser CDP 连通性" rule is parsed
- **Then** the url field SHALL contain "49.234.48.221:9222" and SHALL NOT contain "localhost:9222"

#### Scenario: Cookie rule URL matches infopublisher infra_assets record

- **testable**: true
- **target**: app.py::_init_monitor_tables
- **Given** a fresh SQLite database where both _init_infra_assets() and _init_monitor_tables() have been called
- **When** the config_json of the "小红书 Cookie 有效性" rule is parsed
- **Then** the url field SHALL start with "http://49.234.48.221:8089" and the status_url field SHALL also start with "http://49.234.48.221:8089"
