## ADDED Requirements

### Requirement: Base crawler abstraction layer
系统 SHALL 提供 `BaseCrawler` 抽象基类，定义标准爬取流水线：`fetch_list()` → `parse_list()` → `fetch_detail()` → `parse_detail()` → `normalize()`，每个通过验证的站点实现具体子类。

#### Scenario: Crawler produces normalized output
- **WHEN** 某站点的爬虫模块执行完整流水线
- **THEN** 输出数据包含 title、content、url、source、publish_time、subject、news_type 字段，与 financial_news 表 schema 兼容

#### Scenario: Crawler handles pagination
- **WHEN** 列表页有多页内容
- **THEN** 爬虫自动翻页采集，单次运行最多采集 5 页（可配置）

### Requirement: HTTP mode crawler
系统 SHALL 提供 `HttpCrawler(BaseCrawler)` 实现，基于 requests + BeautifulSoup，适用于静态页面站点。请求间隔 SHALL ≥ 3 秒，使用随机 User-Agent。

#### Scenario: HTTP crawler fetches static page
- **WHEN** 目标站点页面为服务端渲染（非 JavaScript 动态）
- **THEN** HttpCrawler 成功获取 HTML，解析出资讯列表和详情

#### Scenario: HTTP crawler respects rate limit
- **WHEN** HttpCrawler 连续请求多个页面
- **THEN** 每次请求间隔 ≥ 3 秒（+随机抖动 0-2 秒）

### Requirement: Playwright mode crawler
系统 SHALL 提供 `PlaywrightCrawler(BaseCrawler)` 实现，基于 data-agent 现有 playwright 基础设施，适用于动态渲染或中等反爬站点。

#### Scenario: Playwright crawler handles JavaScript rendering
- **WHEN** 目标站点页面内容通过 JavaScript 动态加载
- **THEN** PlaywrightCrawler 等待页面渲染完成后提取内容

#### Scenario: Playwright crawler resource constraint
- **WHEN** Playwright 爬虫启动时
- **THEN** 使用 headless 模式，禁用图片加载（`--disable-images`），单进程运行，采集完成后立即关闭浏览器实例释放内存

### Requirement: Per-site crawler module structure
每个通过验证的站点 SHALL 有独立的爬虫模块文件，包含：
1. 站点配置（URL 模板、CSS 选择器、请求头等）
2. 爬虫类实现（继承 HttpCrawler 或 PlaywrightCrawler）
3. 关键词过滤逻辑（基于赛道关键词）

#### Scenario: Crawler module is self-contained
- **WHEN** 添加一个新站点的爬虫模块
- **THEN** 仅需创建一个 Python 文件（如 `xincailiao.py`），无需修改框架代码

### Requirement: Keyword-based relevance filtering
爬虫 SHALL 对采集到的文章标题进行关键词过滤，仅保留与关联赛道相关的资讯。关键词来源于 tracks 表的赛道名称及其别名。

#### Scenario: Filter irrelevant articles
- **WHEN** 爬虫采集到一篇标题为"旅游行业复苏"的文章，但关联赛道为"新材料"
- **THEN** 该文章被过滤，不写入 financial_news 表

#### Scenario: Accept relevant articles
- **WHEN** 爬虫采集到一篇标题为"碳纤维复合材料在航空航天领域的应用突破"
- **THEN** 该文章通过过滤，subject 标记为对应赛道，写入 financial_news 表

### Requirement: Source field standardization
每个新站点的 source 标识 SHALL 在 data-agent 的 `models.py` 的 `SOURCE_NAMES` 列表中注册，格式为小写英文域名缩写。

#### Scenario: New source registered
- **WHEN** 新站点 xincailiao.com 通过验证并开发爬虫
- **THEN** source 字段值为 "xincailiao"，注册到 SOURCE_NAMES 列表
