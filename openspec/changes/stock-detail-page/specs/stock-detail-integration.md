# Spec: Stock Detail Page Integration

## MODIFIED Requirements

### Requirement: Navigation from Stock Entry Page to Detail

The stock entry page (`/stock`) SHALL provide clickable links from search results and stock list items that navigate to the stock detail sub-view.

#### Scenario: Clicking a search result navigates to detail

- **Given** the user is on the stock entry page (`/stock`)
- **And** the user has performed a search that returned results
- **When** the user clicks on a search result item
- **Then** the SPA SHALL navigate to `/stock/<code>` where `<code>` is the stock code of the clicked item
- **And** the navigation SHALL NOT trigger a full page reload

#### Scenario: Clicking a watchlist stock navigates to detail

- **Given** the user is on the follows/watchlist page (`/follows`)
- **When** the user clicks on a stock item in their watchlist
- **Then** the SPA SHALL navigate to `/stock/<code>` where `<code>` is the stock code of the clicked item

### Requirement: Tab Content Lazy Loading

Each tab in the stock detail view SHALL lazily load its content only when first activated.

#### Scenario: Lazy loading on first visit

- **Given** the user is on the stock detail page with the "实时行情" tab active
- **When** the user clicks the "AI分析" tab for the first time
- **Then** the system SHALL fetch AI analysis data at that moment (not preload all tabs)
- **And** if the user switches back to "实时行情", the previously loaded content SHALL be preserved in memory

#### Scenario: Tab content caching within session

- **Given** the user has visited the "公告" tab and data was loaded
- **When** the user switches away and then back to "公告" tab
- **Then** the previously loaded data SHALL be displayed immediately without re-fetching
- **Unless** the data was loaded more than 60 seconds ago, in which case it SHALL be refreshed
