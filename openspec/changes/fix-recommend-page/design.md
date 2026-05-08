# Design: Fix Recommend Page — Use Available Data Sources

## Architecture Decision

The recommend page currently fails silently because it calls stockshark endpoints whose underlying database tables (industry, concept) are empty. Rather than populating those tables or adding new backend routes, we **reuse existing working proxy routes** that already have data.

This is a **frontend-only change**. No backend modifications needed.

## Data Flow

### View 1: 热门研报 (Hot Reports)

```
Browser → GET /api/stock/reports?keyword=&limit=10
        → Flask stock_reports route (app.py)
        → shark_request → StockShark /api/report/search?keyword=&limit=10
        → Returns: { reports: [{ title, institution, date, category, ... }] }
```

The `stock_reports` route already has caching (`_report_cache`, 5min for empty, 30min for data).

### View 2: 赛道热度 (Track Heat)

```
Browser → GET /api/proxy/tracks/heat/latest
        → Flask proxy_tracks route (app.py)
        → Agent API /api/tracks/heat/latest
        → Returns: track heat scores with trend data
```

This reuses the factory's own track infrastructure — the same data shown on the track page.

### View 3: 主题搜索 (Theme Search)

```
Browser ─┬→ GET /api/stock/reports?keyword={kw}
         │  → StockShark report search
         └→ GET /api/search/by-keyword?keyword={kw}
            → StockShark stock keyword search
```

Two parallel requests, combined results displayed.

## Files to Modify

| File | Change | Scope |
|------|--------|-------|
| `templates/index.html` | Rewrite recommend section JS: `loadRecommend`, `loadRecIndustry`, `loadRecConcept`, `loadRecTheme` | **frontend** |
| `templates/index.html` | Update button labels: 行业精选→热门研报, 概念龙头→赛道热度 | **frontend** |

> **Note**: All frontend tasks (`scope: frontend`) require manual implementation — zsiga will not execute these.

## Backend Routes (No Changes)

| Route | Method | Status |
|-------|--------|--------|
| `/api/stock/reports` | GET | ✅ Existing, cached, working |
| `/api/proxy/tracks/heat/latest` | GET | ✅ Existing, working |
| `/api/search/by-keyword` | GET | ✅ Existing, working |

## UI Layout (Reference)

Three tab buttons at the top of recommend section:
1. **热门研报** — Grid of report cards (title, institution, date, category badge)
2. **赛道热度** — List of track items (name, heat score bar, trend arrow)
3. **主题搜索** — Search input + dual results (reports list + stock matches)
