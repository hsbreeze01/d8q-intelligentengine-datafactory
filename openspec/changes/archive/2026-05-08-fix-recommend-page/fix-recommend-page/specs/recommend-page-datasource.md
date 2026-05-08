# Delta Spec: Recommend Page Data Source Rewrite

## MODIFIED Requirements

### Requirement: Recommend page SHALL display three data-driven views using available data sources

The recommend page SHALL replace the three current views (行业精选/概念龙头/主题投资) with views backed by data sources that have actual data.

#### Scenario: User opens recommend page and sees 热门研报 view (replacing 行业精选)

- **Given** the user navigates to the recommend page
- **When** the page loads and the default view "热门研报" is selected
- **Then** the frontend SHALL call `GET /api/stock/reports?keyword=&limit=10` to fetch the latest research reports
- **And** display report cards showing title, institution, date, and category tags
- **And** if the API returns no reports, display an empty-state message

#### Scenario: User switches to 赛道热度 view (replacing 概念龙头)

- **Given** the user is on the recommend page
- **When** the user selects the "赛道热度" tab
- **Then** the frontend SHALL call `GET /api/proxy/tracks/heat/latest` to fetch track heat data
- **And** display track cards showing name, heat score, and trend indicator
- **And** if the API returns no tracks, display an empty-state message

#### Scenario: User uses 主题搜索 view with keyword input

- **Given** the user is on the recommend page and selects "主题搜索" tab
- **When** the user enters a keyword and submits
- **Then** the frontend SHALL call `GET /api/stock/reports?keyword={keyword}` to search related reports
- **And** the frontend SHALL also call `GET /api/search/by-keyword?keyword={keyword}` to find matching stocks
- **And** display combined results: report cards and stock match cards
- **And** if both APIs return empty, display "未找到相关内容"

### Requirement: Backend proxy routes SHALL remain unchanged

All required backend routes already exist and SHALL NOT be modified:
- `GET /api/stock/reports` — proxies to stockshark report search
- `GET /api/proxy/tracks/heat/latest` — proxies to agent track heat
- `GET /api/search/by-keyword` — proxies to stockshark keyword stock search

#### Scenario: Existing report proxy route is called from recommend page

- **Given** the frontend calls `GET /api/stock/reports?keyword=&limit=10`
- **When** the request reaches the Flask backend
- **Then** the existing `stock_reports` route SHALL proxy to stockshark `/api/report/search`
- **And** return the result with caching as currently implemented

#### Scenario: Existing track heat route is called from recommend page

- **Given** the frontend calls `GET /api/proxy/tracks/heat/latest`
- **When** the request reaches the Flask backend
- **Then** the existing `proxy_tracks` route SHALL proxy to the agent API
- **And** return the track heat data as-is

## REMOVED Requirements

### Requirement: Recommend page SHALL stop calling empty data source APIs

The recommend page SHALL NOT call the following endpoints which return empty data:
- `/api/stock/industries`
- `/api/stock/concepts`
- `/api/stock/sectors` (without a specific symbol)
- `/api/stock/themes` (list all themes)

#### Scenario: Page no longer makes requests to empty endpoints

- **Given** the recommend page is loaded
- **When** any view is active
- **Then** no HTTP request SHALL be made to `/api/stock/industries`, `/api/stock/concepts`, or sector/theme list endpoints
- **And** the browser network tab SHALL NOT show 404/empty responses from these URLs
