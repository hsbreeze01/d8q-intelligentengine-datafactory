## Context

D8Q 平台当前通过财联社（cls.cn）、每日经济新闻（nbd.com.cn）、36氪三个通用财经源采集资讯，写入 `financial_news` 表。现有爬虫基础设施包括：

- **Playwright 爬虫**（cailianshe_mcp）：完整的反检测浏览器自动化，支持搜索、内容提取、质量评估
- **HTTP 爬虫**（nbd_comprehensive）：基于 requests + BeautifulSoup 的轻量级采集
- **调度器**：factory scheduler 每日定时触发 creation 任务，data-agent 执行采集

材料赛道（新材料、碳纤维）当前的资讯覆盖不足：36kr 仅 6 条新材料数据（其中碳纤维 0 条），通用财经源对垂直领域覆盖有限。需要引入材料专业站点，但各站点技术特性差异大（有的有搜索 API，有的需浏览器渲染，有的有强反爬），需先做技术验证。

## Goals / Non-Goals

**Goals:**
- 对 10+ 候选材料站点逐一完成爬取技术验证，输出标准化验证报告
- 验证维度：页面可访问性、列表页/详情页结构可解析性、搜索功能可用性、反爬机制强度、数据质量和密度、更新频率
- 通过验证的站点开发可复用的爬虫模块，统一输出为 `financial_news` 表格式
- 爬虫模块支持两种模式：轻量 HTTP 模式（无需浏览器）和 Playwright 模式（需浏览器渲染）

**Non-Goals:**
- 不改造现有 cailianshe/nbd/36kr 爬虫
- 不做实时推送（仅定时采集）
- 不做付费/注册墙内容采集
- 不做全站历史数据回采（仅采集近期资讯）
- 不新增赛道定义（使用现有 tracks 表中的"新材料"/"碳纤维"）

## Decisions

### 1. 验证流程采用"探针优先"策略

**决策**：每个站点先写一个最小化探针脚本（~50行），测试列表页 HTML 结构、详情页字段完整性、反爬响应，验证通过后再开发完整爬虫模块。

**理由**：材料站点技术差异大，避免在不可行站点上浪费开发时间。探针脚本可复用为爬虫的基础框架。

**替代方案**：直接开发完整爬虫 → 可能大量返工；人工逐站检查 → 无法自动化复现。

### 2. 爬虫模块分层架构

**决策**：采用三层架构：
- `BaseCrawler`：抽象基类，定义 `fetch_list()` → `parse_list()` → `fetch_detail()` → `parse_detail()` → `normalize()` 流水线
- `HttpCrawler(BaseCrawler)`：基于 requests + BeautifulSoup，适用于静态页面站点
- `PlaywrightCrawler(BaseCrawler)`：基于现有 playwright 基础设施，适用于动态渲染/有反爬站点

**理由**：复用 data-agent 已有的 playwright 基础设施；HTTP 模式内存消耗远低于浏览器模式（~10MB vs ~300MB），优先使用 HTTP 模式。

### 3. 验证报告格式标准化

**决策**：每个站点输出统一 JSON 验证报告，包含：
```json
{
  "site": "xincailiao.com",
  "status": "pass|fail|partial",
  "mode": "http|playwright",
  "list_page": { "accessible": true, "items_per_page": 20, "has_pagination": true },
  "detail_page": { "title": true, "content": true, "date": true, "author": false },
  "anti_crawl": { "level": "none|low|medium|high", "notes": "" },
  "search": { "available": true, "by_keyword": true },
  "sample_data": [{ "title": "...", "url": "...", "date": "..." }],
  "recommendation": "适合作为新材料/碳纤维赛道资讯源"
}
```

**理由**：标准化报告便于批量对比决策，也可作为后续爬虫模块的配置基础。

### 4. 候选站点分两批验证

**决策**：
- **第一批**（高优先级，预计技术难度低）：新材料在线、OFweek新材料、ScienceDaily Materials、AZoM
- **第二批**（中优先级，技术难度可能较高）：材料人/材料牛、Phys.org、Advanced Science News、中国复合材料工业协会

**理由**：第一批站点页面结构相对规范，验证成功概率高，可快速产出可用源。第二批站点可能需要浏览器渲染或反爬处理。

## Risks / Trade-offs

- **[反爬封锁风险]** 材料垂直站点可能检测到爬虫并封锁 IP → Mitigation: 控制请求频率（≥3s间隔），使用随机 User-Agent，失败后自动退避；复用现有 ghost browser 反检测能力
- **[页面结构变化]** 网站改版导致爬虫失效 → Mitigation: 使用 CSS selector 配置化而非硬编码，结构变化时只需修改配置
- **[服务器内存压力]** Playwright 模式爬虫与现有 ghost browser 同时运行可能触发 OOM → Mitigation: 优先使用 HTTP 模式；Playwright 爬虫仅在低峰期（如凌晨）执行；与 infopublisher 发布任务错开时间窗口
- **[数据质量]** 部分站点资讯质量参差不齐，可能与赛道不相关 → Mitigation: 爬虫内置关键词过滤（基于 tracks 表的赛道关键词），低相关度文章不入库
- **[法律合规]** 需尊重 robots.txt 和版权 → Mitigation: 验证阶段检查 robots.txt；仅采集公开资讯标题+摘要（非全文）；标注来源 URL
