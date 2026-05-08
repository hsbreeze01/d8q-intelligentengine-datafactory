# Spec: Stock Detail View

## ADDED Requirements

### Requirement: Stock Detail Sub-View

The system SHALL render a stock detail sub-view within the SPA when the URL path matches `/stock/<code>` where `<code>` is a 6-digit stock code or a resolvable stock name.

#### Scenario: User navigates to stock detail from search

- **Given** the user is on the stock entry page
- **When** the user clicks a stock item from search results
- **Then** the SPA SHALL navigate to `/stock/<code>` without a full page reload
- **And** the stock detail view SHALL be rendered inside the existing SPA shell

#### Scenario: User navigates to stock detail from watchlist

- **Given** the user is on the follows (watchlist) page
- **When** the user clicks a stock item in the watchlist
- **Then** the SPA SHALL navigate to `/stock/<code>` without a full page reload

#### Scenario: Direct URL access to stock detail

- **Given** a user enters `/stock/600733` directly in the browser address bar
- **When** the page loads
- **Then** the Flask backend SHALL serve the same `index.html` SPA shell
- **And** the frontend router SHALL detect the path and render the stock detail view

### Requirement: Stock Header Panel

The stock detail view SHALL display a header panel at the top showing the stock's real-time quote information.

#### Scenario: Header panel displays quote data

- **Given** the user is viewing the stock detail page for stock code `600733`
- **When** the view loads
- **Then** the system SHALL call `/api/stock/quote?symbol=<code>` to fetch real-time data
- **And** the header SHALL display the stock name, stock code, current price, change amount, and change percentage
- **And** the header SHALL display up to 12 key indicators (open, high, low, volume, turnover, PE, PB, market cap, total shares, circulating shares, 52-week high, 52-week low)
- **And** positive change SHALL be shown in red, negative in green (Chinese market convention)

#### Scenario: Header panel shows loading state

- **Given** the user navigates to a stock detail page
- **When** the quote data is being fetched
- **Then** the header panel SHALL display a loading skeleton or spinner
- **And** no stale data from a previously viewed stock SHALL be shown

#### Scenario: Header panel shows error state

- **Given** the user navigates to a stock detail page
- **When** the quote API returns an error or times out
- **Then** the header panel SHALL display a user-friendly error message with a retry button
- **And** the tab navigation SHALL still be visible so the user can switch tabs

### Requirement: Breadcrumb Navigation

The stock detail view SHALL display a breadcrumb navigation bar at the top of the content area.

#### Scenario: Breadcrumb with back navigation

- **Given** the user is on the stock detail page for stock `600733` (北汽蓝谷)
- **Then** the breadcrumb SHALL show "个股分析 > 600733 北汽蓝谷"
- **And** a back button SHALL be present in the top-left corner
- **When** the user clicks the back button or the "个股分析" breadcrumb segment
- **Then** the SPA SHALL navigate back to `/stock` (the stock entry page)

### Requirement: Stock Detail Tab Navigation

The stock detail view SHALL provide a tab bar with 6 tabs below the header panel.

#### Scenario: Default tab selection

- **Given** the user navigates to `/stock/600733`
- **When** the view loads
- **Then** the "实时行情" (Real-time Quotes) tab SHALL be selected by default

#### Scenario: Tab switching

- **Given** the user is on the stock detail page
- **When** the user clicks the "公告" (Announcements) tab
- **Then** the tab content area SHALL switch to show announcements content
- **And** the URL SHALL update to `/stock/600733?tab=announcements` (or equivalent hash-based routing)
- **And** the previously active tab content SHALL be unloaded/hidden

#### Scenario: Tab list

The system SHALL provide exactly the following 6 tabs in this order:
1. 实时行情 (Real-time Quotes)
2. 技术分析 (Technical Analysis)
3. AI分析 (AI Analysis)
4. 估值 (Valuation)
5. 公告 (Announcements)
6. 供应链 (Supply Chain)
