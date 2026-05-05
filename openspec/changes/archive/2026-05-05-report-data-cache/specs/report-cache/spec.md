## ADDED Requirements

### Requirement: Report cache with TTL
The system SHALL cache report search results keyed by `(keyword, limit)` with a 30-minute TTL. When a cache hit occurs, the system SHALL return cached data without making any remote API call.

#### Scenario: Cache hit for report search
- **WHEN** a user searches for keyword "北特科技" with limit 20
- **AND** the same search was performed within the last 30 minutes
- **THEN** the system returns the cached result without calling StockShark `/api/report/search`

#### Scenario: Cache miss for report search
- **WHEN** a user searches for keyword "宁德时代" with limit 20
- **AND** no cache entry exists or TTL has expired
- **THEN** the system calls StockShark `/api/report/search?keyword=宁德时代&limit=20`, stores the result in cache, and returns it

#### Scenario: Cache expires after TTL
- **WHEN** a cache entry for keyword "北特科技" was created 31 minutes ago
- **THEN** the system treats it as a cache miss, fetches fresh data, and updates the cache

### Requirement: Announcement cache with TTL
The system SHALL cache announcement data keyed by `(stock_code, days)` with a 15-minute TTL. When a cache hit occurs, the system SHALL return cached data without making any remote API call.

#### Scenario: Cache hit for announcements
- **WHEN** a user queries announcements for stock_code "603009" with days=30
- **AND** the same query was performed within the last 15 minutes
- **THEN** the system returns the cached announcements without calling StockShark

#### Scenario: Cache miss for announcements
- **WHEN** a user queries announcements for stock_code "603009" with days=30
- **AND** no cache entry exists or TTL has expired
- **THEN** the system calls StockShark, caches the result, and returns it

### Requirement: Batch query cache optimization
The system SHALL split batch query keywords into cached and uncached groups before making remote calls. Only uncached keywords SHALL trigger remote API requests.

#### Scenario: Batch search with partial cache hits
- **WHEN** a user batch searches ["北特科技", "璞源材料", "宁德时代"]
- **AND** "北特科技" and "宁德时代" are cached, "璞源材料" is not
- **THEN** the system only makes remote calls for "璞源材料"
- **AND** combines cached results with fresh results in the response

#### Scenario: Batch search with all cache hits
- **WHEN** a user batch searches ["北特科技", "宁德时代"]
- **AND** both are cached and within TTL
- **THEN** the system makes zero remote API calls and returns all cached data

#### Scenario: Batch search with no cache hits
- **WHEN** a user batch searches ["璞源材料", "璞源材料2"]
- **AND** neither is cached
- **THEN** the system makes remote calls for all keywords and caches each result

### Requirement: Empty result caching
The system SHALL cache empty results (no reports found) with a 5-minute TTL to prevent repeated requests for non-existent data.

#### Scenario: Cache empty result
- **WHEN** a user searches for a keyword that returns zero reports
- **THEN** the system caches the empty result with a 5-minute TTL
- **AND** subsequent searches for the same keyword within 5 minutes return the cached empty result without remote calls

### Requirement: Cache hit statistics in response headers
The system SHALL include cache hit statistics in the HTTP response header `X-Cache-Hits` for monitoring purposes.

#### Scenario: Cache statistics reported
- **WHEN** a batch search for 5 keywords returns 3 from cache and 2 from remote
- **THEN** the response includes header `X-Cache-Hits: 3/5`

### Requirement: API contract unchanged
The system SHALL maintain identical request and response format for `/api/report/stock` and `/api/report/search`. Caching is transparent to the frontend.

#### Scenario: Response format identical with cache
- **WHEN** a search request is served from cache
- **THEN** the response JSON structure is identical to a non-cached response

### Requirement: Shared cache across users
The system SHALL NOT isolate cached data by user. All users share the same cache entries for the same keyword. User-level filtering (which stocks to show) is handled by the frontend.

#### Scenario: Two users search same keyword
- **WHEN** user A searches "北特科技" and the result is cached
- **AND** user B searches "北特科技" within the TTL
- **THEN** user B receives the cached data from user A's query
