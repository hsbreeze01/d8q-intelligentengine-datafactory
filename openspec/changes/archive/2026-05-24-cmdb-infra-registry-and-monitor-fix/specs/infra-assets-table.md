# Spec: infra_assets CMDB Table

## ADDED Requirements

### Requirement: infra_assets table creation

The system SHALL create an `infra_assets` table on application startup via a dedicated
initialization function `_init_infra_assets()`. The table MUST be created before
`_init_monitor_tables()` so that monitor rules can reference infra_assets data.

Table schema:

| Column         | Type     | Constraints                                         |
|----------------|----------|-----------------------------------------------------|
| id             | INTEGER  | PRIMARY KEY AUTOINCREMENT                            |
| name           | TEXT     | NOT NULL, UNIQUE — human-readable service name      |
| host           | TEXT     | NOT NULL — IP or hostname                           |
| port           | INTEGER  | NOT NULL                                            |
| health_path    | TEXT     | NOT NULL DEFAULT ''                                 |
| service_type   | TEXT     | NOT NULL DEFAULT 'http' — one of http/cdp/db/systemd |
| group_name     | TEXT     | NOT NULL DEFAULT 'd8q'                              |
| env            | TEXT     | NOT NULL DEFAULT 'production'                       |
| enabled        | INTEGER  | NOT NULL DEFAULT 1                                  |
| metadata_json  | TEXT     | DEFAULT '{}'                                        |
| created_at     | DATETIME | DEFAULT (datetime('now'))                           |
| updated_at     | DATETIME | DEFAULT (datetime('now'))                           |

#### Scenario: infra_assets table exists after init

- **testable**: true
- **target**: app.py::_init_infra_assets
- **Given** a fresh SQLite database with no infra_assets table
- **When** `_init_infra_assets()` is called
- **Then** the `infra_assets` table SHALL exist with columns: id, name, host, port, health_path, service_type, group_name, env, enabled, metadata_json, created_at, updated_at

#### Scenario: infra_assets table is idempotent

- **testable**: true
- **target**: app.py::_init_infra_assets
- **Given** a SQLite database where `infra_assets` table already exists with builtin data
- **When** `_init_infra_assets()` is called again
- **Then** no duplicate rows SHALL be inserted; the builtin row count remains the same

---

### Requirement: 7 builtin service records

When the `infra_assets` table is empty (count = 0), `_init_infra_assets()` SHALL insert
exactly 7 builtin service records. The system MUST use `INSERT OR IGNORE` or an
idempotent guard to prevent duplicate inserts on repeated startup.

Builtin records (name → host, port, health_path, service_type):

| name            | host            | port | health_path      | service_type |
|-----------------|-----------------|------|------------------|--------------|
| factory         | localhost       | 8088 | /                | http         |
| agent           | localhost       | 8000 | /api/health      | http         |
| compass         | localhost       | 8087 | /health          | http         |
| stockshark      | 49.234.48.221   | 5000 | /health          | http         |
| infopublisher   | 49.234.48.221   | 8089 | /api/health      | http         |
| ghost_browser   | 49.234.48.221   | 9222 | /json/version    | cdp          |
| mysql           | localhost       | 3306 |                  | db           |

#### Scenario: 7 builtin records inserted on fresh database

- **testable**: true
- **target**: app.py::_init_infra_assets
- **Given** a fresh SQLite database with no rows in infra_assets
- **When** `_init_infra_assets()` is called
- **Then** exactly 7 rows SHALL exist in infra_assets with the names: factory, agent, compass, stockshark, infopublisher, ghost_browser, mysql

#### Scenario: ghost_browser record uses direct remote CDP address

- **testable**: true
- **target**: app.py::_init_infra_assets
- **Given** a fresh SQLite database
- **When** `_init_infra_assets()` is called
- **Then** the `ghost_browser` row SHALL have host='49.234.48.221', port=9222, service_type='cdp' — NOT localhost:9222

#### Scenario: mysql record has service_type db

- **testable**: true
- **target**: app.py::_init_infra_assets
- **Given** a fresh SQLite database
- **When** `_init_infra_assets()` is called
- **Then** the `mysql` row SHALL have service_type='db' and host='localhost'
