## ADDED Requirements

### Requirement: 量科网爬虫
系统 SHALL 实现量科网（qtc.com.cn）新闻爬虫，采集量子科技相关文章。

#### Scenario: 采集量科网文章列表
- **WHEN** 调用量科网爬虫函数
- **THEN** 系统请求 `qtc.com.cn/news` 页面，解析静态 HTML 获取文章列表（标题、URL、日期）

#### Scenario: 返回标准格式
- **WHEN** 爬虫采集到文章
- **THEN** 每条返回 `{title, url, source: "qtc", content, date_text}` 格式

#### Scenario: 支持关键词过滤
- **WHEN** 传入关键词参数
- **THEN** 返回标题或内容包含关键词的文章（不区分中英文大小写）

### Requirement: C114 量子频道爬虫
系统 SHALL 实现 C114 通信网量子频道爬虫。

#### Scenario: 采集 C114 量子频道
- **WHEN** 调用 C114 爬虫函数
- **THEN** 系统请求 `c114.com.cn/quantum` 页面（GBK 编码），解析新闻列表

#### Scenario: 处理 GBK 编码
- **WHEN** 接收到 C114 页面响应
- **THEN** 使用 `resp.encoding = 'gbk'` 正确解码中文字符

### Requirement: IT之家搜索爬虫
系统 SHALL 实现 IT之家量子计算搜索爬虫。

#### Scenario: 通过搜索 API 获取结果
- **WHEN** 调用 IT之家爬虫函数
- **THEN** 系统请求 IT之家搜索 API，获取包含"量子计算"关键词的新闻列表

#### Scenario: API 返回 JSON 解析
- **WHEN** API 返回 JSON 响应
- **THEN** 解析 newslist 数组，提取 title、url、内容摘要、发布时间

### Requirement: 爬虫注册到采集系统
系统 SHALL 将量子爬虫注册到多源采集框架中。

#### Scenario: CRAWL_MAP 注册
- **WHEN** multi_source_crawl.py 加载
- **THEN** `_CRAWL_MAP` 包含 "qtc"、"c114"、"ithome" 三个源的爬虫函数

#### Scenario: ACTIVE_SOURCES 启用
- **WHEN** multi_source_crawl.py 加载
- **THEN** `ACTIVE_SOURCES` 包含 "qtc"、"c114"、"ithome"

#### Scenario: 赛道默认源映射
- **WHEN** 采集任务的主题为"量子计算"
- **THEN** `get_default_sources_for_subject("量子计算")` 返回 `["qtc", "c114", "ithome"]`
