## 1. 验证框架搭建

- [x] 1.1 在 data-agent 中创建 `src/intelligent_data_agent/crawlers/material/` 目录结构，包含 `__init__.py`、`base.py`（BaseCrawler/HttpCrawler/PlaywrightCrawler 抽象层）
- [x] 1.2 实现 `base.py` 中的 `BaseCrawler` 抽象基类，定义 `fetch_list()` → `parse_list()` → `fetch_detail()` → `parse_detail()` → `normalize()` 流水线，输出与 `financial_news` 表 schema 兼容的标准化字典
- [x] 1.3 实现 `HttpCrawler(BaseCrawler)`，基于 requests + BeautifulSoup，内置请求间隔 ≥ 3s + 随机抖动 + 随机 User-Agent
- [x] 1.4 实现 `PlaywrightCrawler(BaseCrawler)`，基于 data-agent 现有 playwright 基础设施，headless 模式 + 禁用图片加载 + 单进程 + 完成后关闭浏览器实例
- [x] 1.5 创建验证探针模板 `validation_probe.py`，输出标准化 JSON 验证报告（site, status, mode, list_page, detail_page, anti_crawl, search, sample_data, recommendation）
- [x] 1.6 在 `models.py` 的 `SOURCE_NAMES` 列表中预留新站点标识位（xincailiao, ofweek, cailiaoren, sciencedaily, azom, physorg 等）

## 2. 第一批站点技术验证（高优先级）

- [x] 2.1 新材料在线（xincailiao.com）验证探针：测试资讯列表页结构、详情页字段、搜索功能、反爬强度、采集 5 条样本数据
- [x] 2.2 OFweek 新材料（materials.ofweek.com）验证探针：同上验证流程
- [x] 2.3 ScienceDaily Materials（sciencedaily.com/matter_energy/materials/）验证探针：同上验证流程
- [x] 2.4 AZoM（azom.com）验证探针：同上验证流程
- [x] 2.5 汇总第一批验证报告，标注 pass/partial/fail，输出到验证报告目录

## 3. 第二批站点技术验证（中优先级）

- [x] 3.1 材料人/材料牛（cailiaoren.com）验证探针：同上验证流程
- [x] 3.2 Phys.org Materials（phys.org/materials-science/）验证探针：同上验证流程
- [x] 3.3 Advanced Science News（advancedsciencenews.com）验证探针：同上验证流程
- [x] 3.4 中国复合材料工业协会（cspcm.org.cn 或类似）验证探针：同上验证流程
- [x] 3.5 汇总第二批验证报告，合并输出完整验证清单

## 4. 通过验证站点的爬虫模块开发

- [x] 4.1 基于验证结果，为每个 pass 状态的站点创建专用爬虫模块（继承 HttpCrawler 或 PlaywrightCrawler），包含站点配置（URL 模板、CSS 选择器、请求头）
- [x] 4.2 为每个爬虫模块实现关键词过滤逻辑，基于 tracks 表中"新材料"/"碳纤维"赛道的关键词进行相关性过滤
- [x] 4.3 为每个爬虫模块实现 `normalize()` 方法，确保输出字段完整（title, content, url, source, publish_time, subject, news_type）
- [x] 4.4 为 partial 状态但可用的站点开发爬虫模块，标注已知限制（如字段缺失、需特殊处理）

## 5. 集成与调度

- [x] 5.1 在 data-agent scheduler 中注册新材料爬虫模块，配置采集频率（建议每日 1 次，与现有采集错峰）
- [x] 5.2 将采集结果写入 `financial_news` 表，source 字段使用站点标识，subject 字段关联"新材料"或"碳纤维"赛道
- [x] 5.3 验证端到端流水线：采集 → 过滤 → 入库 → 在 D8Q 前端可查看新材料资讯
- [x] 5.4 更新 data-agent README 或文档，记录新增材料垂直源及使用说明
