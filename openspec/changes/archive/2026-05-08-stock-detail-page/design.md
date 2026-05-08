# Design: Stock Detail Page Sub-View

## Architecture Decision

**Decision**: Implement the stock detail as a client-side SPA sub-view within the existing `index.html`, using hash-based or history-based routing consistent with the existing SPA pattern.

**Rationale**: The project already serves a single `index.html` for all routes (`/`, `/stock`, `/follows`, etc.) via Flask. The frontend is a vanilla JS SPA. Adding the stock detail as a sub-view avoids introducing a new framework and maintains consistency. No backend template changes needed — only a new Flask route and frontend JS/HTML additions.

## Data Flow

```
User clicks stock item (search/watchlist)
  → Frontend router detects /stock/<code> path
  → Fetches /api/stock/quote?symbol=<code> for header panel
  → Renders header panel with quote data
  → Renders tab bar, default "实时行情" active
  → Lazy-fetches tab-specific data on tab activation:
      实时行情 → K-line chart data (existing/proxied API)
      技术分析 → Technical indicator data (via Shark API proxy)
      AI分析  → POST /api/stock/comprehensive
      估值    → Valuation data (from quote response)
      公告    → GET /api/stock/announcements?stock_code=<code>
      供应链  → Supply chain data (via Shark API proxy)
```

## Backend Changes

### 1. New Flask route for `/stock/<code>`
- Add `@app.route("/stock/<code>")` to serve the same `index.html`
- This is a minimal change — just one more route decorator pointing to the existing template

### 2. Existing APIs (no changes needed)
- `GET /api/stock/quote?symbol=<code>` — Already exists, returns real-time quote
- `POST /api/stock/comprehensive` — Already exists, returns AI analysis
- `GET /api/stock/announcements?stock_code=<code>` — Already exists
- `GET /api/stock/reports?keyword=<keyword>` — Already exists
- `resolve_stock()` — Already handles name→code resolution

### 3. New proxy endpoints (if needed for K-line / technical data)
- `GET /api/stock/kline?symbol=<code>&period=<period>` — Proxy to Shark API for K-line data
- `GET /api/stock/technical?symbol=<code>` — Proxy to Shark API for technical indicators
- `GET /api/stock/valuation?symbol=<code>` — Proxy to Shark API for valuation data
- `GET /api/stock/supply-chain?symbol=<code>` — Proxy to Shark API for supply chain data

These endpoints follow the existing proxy pattern (`shark_request` helper).

## Frontend Changes

All changes are within `templates/index.html` (the SPA file).

### 1. Router extension
- Extend the existing hash/path-based router to handle `/stock/<code>` and `/stock/<code>?tab=<tab>`
- Store current stock code and tab in app state

### 2. Stock Detail View Component
- New JS object/module `StockDetailView` with:
  - `render(code, tab)` — Renders the full stock detail view
  - `renderHeader(quoteData)` — Renders the header panel
  - `renderTabs(activeTab)` — Renders the tab navigation
  - `renderTabContent(tab, data)` — Dispatches to specific tab renderers

### 3. Tab Content Renderers
- `RealtimeTab` — K-line chart (using lightweight-charts or ECharts) + indicators panel
- `TechnicalTab` — MACD/KDJ/RSI charts + signal summary
- `AITab` — Markdown-rendered AI analysis with loading state
- `ValuationTab` — Valuation metrics table/comparison
- `AnnouncementTab` — Announcements list with expand/collapse
- `SupplyChainTab` — Supply chain relationship list

### 4. CSS Styles
- New section in `<style>` for stock detail layout
- Header panel: flex layout, responsive grid for 12 indicators
- Tab bar: horizontal scrollable tabs (consistent with existing tab styles)
- Tab content: responsive container with loading/error states

### 5. Integration with existing views
- Stock search results: add `onclick` handlers that call `router.navigate('/stock/' + code)`
- Watchlist items: add `onclick` handlers similarly

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `app.py` | MODIFY | Add route `@app.route("/stock/<code>")` to serve index.html |
| `app.py` | MODIFY | Add proxy endpoints for kline, technical, valuation, supply-chain if Shark API supports them |
| `templates/index.html` | MODIFY | Add stock detail view HTML structure, CSS styles, JS router extension, tab renderers, and K-line chart integration |

## Third-party Dependencies

- **K-line Chart**: Use ECharts (if already included) or lightweight-charts CDN. Check existing `index.html` for already-loaded libraries.
- No new Python dependencies needed.

## Key Design Patterns

1. **Proxy pattern**: All external API calls go through Flask proxy endpoints (consistent with existing `shark_request` / `agent_request`)
2. **Lazy loading**: Tab content is fetched only when first activated, cached for 60 seconds
3. **SPA routing**: Hash-based or pushState routing within existing router framework
4. **Error resilience**: Each tab handles errors independently; one tab failure does not block others
5. **Cache reuse**: Leverage existing `ReportCache` and `_report_cache` for announcement/report data
