## Why

量子计算赛道（id=6）已入库 55 个关键词，但缺少专用资讯源。当前通用源（财联社/每经网/36氪）覆盖的是财经科技领域，量子计算的专业资讯分散在垂直网站，通用源命中率低。需要为量子计算赛道增加专用爬虫源。

## What Changes

新增 3 个专用爬虫模块（可行性已验证）：

1. **量科网 qtc.com.cn** — 静态 HTML，文章列表清晰，有分类（量子计算/通信/传感/物理），最佳量子专业源
2. **C114 通信网 c114.com.cn/quantum** — 静态 HTML，量子频道页面结构清晰，含新闻列表和日期
3. **IT之家 ithome.com** — 标签页面需 JS 渲染（404 on direct fetch），但提供 RSS 搜索接口可替代

暂不实现：
- **新华网 news.cn/liangzi** — 新华网结构复杂，需要确认具体频道 URL 格式，作为后续迭代
- **传感器专家网 sensorexpert.com.cn** — 该站是传感器产品平台，量子相关资讯极少且无专门频道，ROI 低

在 data-agent 中：
- 新增 `crawlers/quantum/` 目录，包含 `qtc.py`、`c114.py`、`ithome.py` 及 `runner.py`
- 在 `multi_source_crawl.py` 的 `_CRAWL_MAP` 和 `_TRACK_DEFAULT_SOURCES` 中注册新源
- 在 `ACTIVE_SOURCES` 中启用新源

## Capabilities

### New Capabilities
- `quantum-crawlers`: 量子计算专用资讯爬虫模块（量科网 + C114 + IT之家）

### Modified Capabilities
（无已有 spec 需要修改）

## Impact

- **后端 data-agent**: 新增 crawlers/quantum/ 目录，修改 multi_source_crawl.py 注册新源
- **前端**: 无变更（数据驱动）
- **服务器资源**: 3 个新爬虫在调度任务中运行，预计每次采集 ~60s，内存影响可忽略
