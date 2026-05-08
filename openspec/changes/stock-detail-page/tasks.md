# Tasks: Stock Detail Page

## 1. Backend Route & Proxy Endpoints

- [x] 1.1 Add Flask route `/stock/<code>` in `app.py` to serve `index.html` for any stock code (1 file: `app.py`)
- [ ] 1.2 Add proxy endpoint `GET /api/stock/kline` in `app.py` — fetches K-line data from Shark API and returns it (1 file: `app.py`)
- [ ] 1.3 Add proxy endpoint `GET /api/stock/technical` in `app.py` — fetches technical indicators (MACD/KDJ/RSI) from Shark API (1 file: `app.py`)
- [ ] 1.4 Add proxy endpoint `GET /api/stock/valuation` in `app.py` — fetches valuation data from Shark API (1 file: `app.py`)
- [ ] 1.5 Add proxy endpoint `GET /api/stock/supply-chain` in `app.py` — fetches supply chain relationships from Shark API (1 file: `app.py`)

## 2. Frontend Router & View Shell

- [ ] 2.1 Extend the SPA router in `index.html` to handle `/stock/<code>` path and optional `?tab=` query parameter (1 file: `templates/index.html`)
- [ ] 2.2 Add breadcrumb navigation component with back button and "个股分析 > {code} {name}" display (1 file: `templates/index.html`)
- [ ] 2.3 Add stock header panel HTML structure and CSS — displays price, change, and 12 indicators in responsive grid (1 file: `templates/index.html`)
- [ ] 2.4 Add header panel JS logic — call `/api/stock/quote`, populate data, handle loading/error states (1 file: `templates/index.html`)

## 3. Tab Navigation Framework

- [ ] 3.1 Add tab bar HTML structure and CSS for 6 tabs (实时行情/技术分析/AI分析/估值/公告/供应链) (1 file: `templates/index.html`)
- [ ] 3.2 Implement tab switching JS logic — update URL, lazy-load content, cache loaded data with 60s TTL (1 file: `templates/index.html`)

## 4. Tab Content — 实时行情 (Real-time Quotes)

- [ ] 4.1 Integrate K-line chart library (ECharts or lightweight-charts via CDN) and render candlestick chart with MA overlays (1 file: `templates/index.html`)
- [ ] 4.2 Add K-line period switcher (日K/周K/月K) and wire to `/api/stock/kline` with period parameter (1 file: `templates/index.html`)
- [ ] 4.3 Add core indicators panel below K-line chart — display 12 metrics from quote data in a grid layout (1 file: `templates/index.html`)

## 5. Tab Content — 技术分析 / AI分析 / 估值

- [ ] 5.1 Implement 技术分析 tab renderer — fetch `/api/stock/technical`, display MACD/KDJ/RSI charts and signal summary (1 file: `templates/index.html`)
- [ ] 5.2 Implement AI分析 tab renderer — POST `/api/stock/comprehensive`, render markdown result with loading animation (1 file: `templates/index.html`)
- [ ] 5.3 Implement 估值 tab renderer — fetch `/api/stock/valuation`, display PE/PB/PS metrics and industry comparison (1 file: `templates/index.html`)

## 6. Tab Content — 公告 / 供应链

- [ ] 6.1 Implement 公告 tab renderer — fetch `/api/stock/announcements`, display list with title/date/type, support expand and AI summary toggle (1 file: `templates/index.html`)
- [ ] 6.2 Implement 供应链 tab renderer — fetch `/api/stock/supply-chain`, display upstream/downstream relationships, link to other stock detail pages (1 file: `templates/index.html`)

## 7. Integration with Existing Views

- [ ] 7.1 Add click handlers to stock search results on `/stock` entry page — navigate to `/stock/<code>` (1 file: `templates/index.html`)
- [ ] 7.2 Add click handlers to watchlist items on `/follows` page — navigate to `/stock/<code>` (1 file: `templates/index.html`)

## 8. Testing & Polish

- [ ] 8.1 Add smoke test for new Flask route `/stock/<code>` returning 200 and index.html content (1 file: `tests/test_smoke.py`)
- [ ] 8.2 Add smoke test for new proxy endpoints (`/api/stock/kline`, `/api/stock/technical`, etc.) returning proper error structure when Shark API is unavailable (1 file: `tests/test_smoke.py`)
- [ ] 8.3 Visual review and responsive CSS adjustments for mobile viewport (1 file: `templates/index.html`)
