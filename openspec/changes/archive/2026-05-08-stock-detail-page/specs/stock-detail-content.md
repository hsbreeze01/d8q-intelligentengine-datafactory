# Spec: Stock Detail Tab Content

## ADDED Requirements

### Requirement: Real-time Quotes Tab

The "实时行情" tab SHALL display a K-line chart and a core indicators panel.

#### Scenario: K-line chart rendering

- **Given** the user is viewing the "实时行情" tab for stock `600733`
- **When** the tab content loads
- **Then** the system SHALL fetch K-line data from the backend
- **And** the chart SHALL render candlestick (K-line) data with at least daily granularity
- **And** the chart SHALL support MA5, MA10, MA20 moving average overlays
- **And** the chart SHALL be responsive to the container width

#### Scenario: K-line chart period switching

- **Given** the K-line chart is rendered
- **When** the user selects a different time period (日K, 周K, 月K)
- **Then** the chart SHALL reload with the corresponding period data
- **And** the transition SHALL not cause a full page re-render

#### Scenario: Core indicators panel

- **Given** the "实时行情" tab is active
- **When** the quote data has been loaded
- **Then** the system SHALL display a core indicators panel below or beside the K-line chart
- **And** the panel SHALL show key metrics including: 今开, 昨收, 最高, 最低, 成交量, 成交额, 换手率, 量比, 振幅, 市盈率(PE), 市净率(PB), 总市值

### Requirement: Technical Analysis Tab

The "技术分析" tab SHALL display technical indicator charts and signals.

#### Scenario: Technical indicators display

- **Given** the user switches to the "技术分析" tab
- **When** the tab content loads
- **Then** the system SHALL fetch technical analysis data from the backend
- **And** SHALL display MACD, KDJ, and RSI indicator charts
- **And** SHALL display a summary of technical signals (买入/卖出/中性)

#### Scenario: Technical analysis loading state

- **Given** the user switches to the "技术分析" tab
- **When** data is being fetched
- **Then** a loading placeholder SHALL be shown
- **And** if the data fetch fails, an error message with retry option SHALL be shown

### Requirement: AI Analysis Tab

The "AI分析" tab SHALL trigger and display AI-generated stock analysis.

#### Scenario: AI analysis generation

- **Given** the user switches to the "AI分析" tab for stock `600733`
- **When** the tab content loads
- **Then** the system SHALL call `/api/stock/comprehensive` to request AI-generated analysis
- **And** SHALL display the analysis result as formatted markdown content
- **And** the analysis SHALL include sections for: 综合评估, 投资亮点, 风险提示, 操作建议

#### Scenario: AI analysis loading

- **Given** the user is on the "AI分析" tab
- **When** the AI analysis request is in progress (may take several seconds)
- **Then** a loading animation with progress indicator SHALL be displayed
- **And** the user SHALL be informed that AI analysis is being generated

### Requirement: Valuation Tab

The "估值" tab SHALL display valuation metrics and comparisons.

#### Scenario: Valuation data display

- **Given** the user switches to the "估值" tab
- **When** the tab content loads
- **Then** the system SHALL display valuation indicators: PE(TTM), PE(静), PB, PS, and industry comparison
- **And** SHALL indicate whether the current valuation is above or below industry average

### Requirement: Announcements Tab

The "公告" tab SHALL display recent company announcements.

#### Scenario: Announcements listing

- **Given** the user switches to the "公告" tab for stock `600733`
- **When** the tab content loads
- **Then** the system SHALL call `/api/stock/announcements?stock_code=<code>` to fetch recent announcements
- **And** SHALL display announcements in reverse chronological order with title, date, and type
- **And** the user SHALL be able to expand an announcement to view its detail or AI summary

#### Scenario: AI summary for announcements

- **Given** the announcements tab is showing a list of announcements
- **When** the user requests AI summary (via toggle or button)
- **Then** the system SHALL call `/api/stock/announcements?stock_code=<code>&ai_summary=true`
- **And** SHALL display the AI-generated summary at the top of the announcements list

### Requirement: Supply Chain Tab

The "供应链" tab SHALL display supply chain relationships for the stock.

#### Scenario: Supply chain visualization

- **Given** the user switches to the "供应链" tab
- **When** the tab content loads
- **Then** the system SHALL display upstream suppliers and downstream customers
- **And** each entity SHALL show the company name and relationship type
- **And** clicking a related company SHALL navigate to that company's stock detail page if it is a listed company

## MODIFIED Requirements

### Requirement: Flask Route for SPA Stock Detail

The Flask backend SHALL serve the SPA `index.html` for stock detail URLs.

#### Scenario: Stock detail URL serves SPA shell

- **Given** the Flask application receives a request for `/stock/<code>` where `<code>` is any string
- **When** the route is matched
- **Then** the server SHALL return the same `index.html` content
- **And** the frontend router SHALL handle the path-based routing client-side
