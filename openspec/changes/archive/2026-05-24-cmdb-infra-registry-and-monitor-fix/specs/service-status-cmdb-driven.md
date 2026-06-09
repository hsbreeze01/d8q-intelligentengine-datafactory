# Spec: Service Status API CMDB-Driven

## MODIFIED Requirements

### Requirement: service_status API reads from infra_assets

The `/api/service-status` endpoint SHALL dynamically read the service list from the
`infra_assets` table (WHERE enabled=1) instead of using a hardcoded `http_services`
dictionary. For each row, the endpoint SHALL construct the health-check URL from
`host`, `port`, and `health_path` columns.

The response JSON structure MUST remain backward-compatible: top-level keys `timestamp`
and `services` (dict of service name → status object). Each service status object SHALL
contain at minimum: `status` (ok|error|down), `type` (from service_type column), and `port`.

#### Scenario: service_status returns correct JSON envelope

- **testable**: true
- **target**: app.py::service_status
- **Given** a test Flask app with infra_assets containing the 7 builtin records and all external services mocked
- **When** `GET /api/service-status` is called
- **Then** the response SHALL be HTTP 200 with JSON keys `timestamp` (string) and `services` (dict)

#### Scenario: service_status includes all enabled infra_assets services

- **testable**: true
- **target**: app.py::service_status
- **Given** a test Flask app with infra_assets containing the 7 builtin records (all enabled=1) and all external services mocked
- **When** `GET /api/service-status` is called
- **Then** the `services` dict SHALL contain keys: factory, agent, compass, stockshark, infopublisher, ghost_browser

#### Scenario: service_status excludes disabled infra_assets

- **testable**: true
- **target**: app.py::service_status
- **Given** a test Flask app where infra_assets has `factory` record with enabled=0
- **When** `GET /api/service-status` is called
- **Then** the `services` dict SHALL NOT contain a `factory` key

---

### Requirement: CDP service_type health check

When `infra_assets` contains a row with `service_type='cdp'`, the service_status endpoint
SHALL perform an HTTP GET to `http://{host}:{port}{health_path}` (e.g.
`http://49.234.48.221:9222/json/version`). The result status object SHALL include
`type: "cdp"` (NOT `type: "cdp_tunnel"`).

This replaces the previous hardcoded SSH-tunnel-based detection via `localhost:9222`.

#### Scenario: ghost_browser has type cdp not cdp_tunnel

- **testable**: true
- **target**: app.py::service_status
- **Given** a test Flask app with infra_assets ghost_browser row (service_type=cdp) and the CDP endpoint mocked to return success
- **When** `GET /api/service-status` is called
- **Then** `services.ghost_browser.type` SHALL equal "cdp" and SHALL NOT equal "cdp_tunnel"

---

### Requirement: monitor_status API reads from infra_assets

The `/api/monitor/status` endpoint's inline `http_svcs` dictionary (duplicated from
service_status) SHALL also be replaced by reading from `infra_assets`. The service
health-check logic in monitor_status SHALL use the same CMDB-driven approach as
service_status.

The response JSON structure MUST remain backward-compatible: top-level keys `services`,
`rules`, `alert_count`, `timestamp`.

#### Scenario: monitor_status returns backward-compatible JSON structure

- **testable**: true
- **target**: app.py::monitor_status
- **Given** a test Flask app with infra_assets and monitor_rules initialized, admin session, and all external services mocked
- **When** `GET /api/monitor/status` is called
- **Then** the response SHALL be HTTP 200 with JSON keys `services`, `rules`, `alert_count`, `timestamp`

#### Scenario: monitor_status ghost_browser uses direct CDP address

- **testable**: true
- **target**: app.py::monitor_status
- **Given** a test Flask app with infra_assets ghost_browser row (host=49.234.48.221, port=9222) and the CDP endpoint at that address mocked to return success
- **When** `GET /api/monitor/status` is called
- **Then** `services.ghost_browser` SHALL have `status: "active"` or `status: "ok"` and `type: "cdp"`, and SHALL NOT use localhost:9222
