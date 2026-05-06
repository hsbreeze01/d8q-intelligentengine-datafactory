## 1. 爬虫模块开发

- [ ] 1.1 创建 `crawlers/quantum/__init__.py` 和 `base.py`（公共 session、解析工具函数）
- [ ] 1.2 实现 `crawlers/quantum/qtc.py`（量科网爬虫，解析 qtc.com.cn/news 静态 HTML）
- [ ] 1.3 实现 `crawlers/quantum/c114.py`（C114 量子频道爬虫，GBK 编码处理）
- [ ] 1.4 实现 `crawlers/quantum/ithome.py`（IT之家搜索 API 爬虫，JSON 解析）
- [ ] 1.5 实现 `crawlers/quantum/runner.py`（统一入口 `get_quantum_news`）

## 2. 注册到采集系统

- [ ] 2.1 在 `multi_source_crawl.py` 的 `_CRAWL_MAP` 中注册 qtc、c114、ithome
- [ ] 2.2 在 `ACTIVE_SOURCES` 中添加三个新源
- [ ] 2.3 在 `_TRACK_DEFAULT_SOURCES` 中添加 `"量子计算": ["qtc", "c114", "ithome"]`
- [ ] 2.4 新增 `_crawl_qtc`、`_crawl_c114`、`_crawl_ithome` 三个调度函数

## 3. 集成验证

- [ ] 3.1 本地测试各爬虫可独立运行并返回正确格式数据
- [ ] 3.2 部署到服务器，重启 data-agent
- [ ] 3.3 创建量子计算赛道的采集任务并执行，验证新源参与采集
- [ ] 3.4 提交并推送代码变更
