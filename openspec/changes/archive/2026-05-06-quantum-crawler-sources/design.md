## Context

现有爬虫架构：
- `crawlers/material/` — 材料科学爬虫包（5源），使用 `requests` + `BeautifulSoup`，结构为 `base.py`（公共函数）+ 各源文件 + `runner.py`（统一入口）
- `multi_source_crawl.py` 中的 `_CRAWL_MAP` 注册爬虫函数，`ACTIVE_SOURCES` 控制启用，`_TRACK_DEFAULT_SOURCES` 映射赛道默认源

新源分析结果：

| 源 | URL | 类型 | 难度 | 特点 |
|---|---|---|---|---|
| 量科网 | qtc.com.cn/news | 静态 HTML | Easy | 专业量子站，分类清晰（量子计算/通信/传感/物理），文章列表含标题+日期 |
| C114 量子 | c114.com.cn/quantum | 静态 HTML | Easy | 通信网量子频道，新闻列表含标题+摘要+日期，GBK 编码 |
| IT之家 | ithome.com | RSS | Easy | 标签页需 JS 渲染，但可通过 RSS 接口 `https://api.ithome.com/json/newslist/news?word=量子计算` 获取 |

## Goals / Non-Goals

**Goals:**
- 3 个量子专用爬虫：量科网、C114、IT之家
- 量科网作为主力源（量子专业，覆盖面最广）
- 统一返回格式与现有爬虫一致

**Non-Goals:**
- 新华网量子频道（URL 结构待确认，后续迭代）
- 传感器专家网（量子资讯极少，ROI 低）
- Playwright/Selenium 渲染（暂不引入，3 个源都不需要）

## Decisions

### 1. 爬虫包结构：`crawlers/quantum/`

复用 material 爬虫的包结构：
```
crawlers/quantum/
  __init__.py
  base.py       # 公共 HTTP session、解析工具
  qtc.py        # 量科网爬虫
  c114.py       # C114 量子频道爬虫
  ithome.py     # IT之家搜索爬虫（RSS API）
  runner.py     # 统一入口 get_quantum_news(keyword, max_results)
```

### 2. IT之家使用 RSS API 而非页面抓取

**选择**：通过 IT之家 API `https://api.ithome.com/json/newslist/news?word=量子计算` 获取搜索结果。

**理由**：标签页面 `ithome.com/tag/量子计算` 返回 404（需 JS 渲染），但搜索 API 直接返回 JSON，无需渲染引擎。

### 3. C114 使用 GBK 编码

**选择**：C114 页面使用 GBK 编码，`resp.encoding = 'gbk'` 后再解析。

### 4. 赛道默认源映射

```python
_TRACK_DEFAULT_SOURCES = {
    ...
    "量子计算": ["qtc", "c114", "ithome"],
}
```

## Risks / Trade-offs

- **量科网反爬** → 目前无可见反爬措施，设置合理 User-Agent 和请求间隔即可
- **C114 编码问题** → GBK 编码需显式设置，否则中文乱码
- **IT之家 API 变更** → 搜索 API 非官方公开接口，可能变更。如失效可降级为手动搜索 RSS
