## Why

当前 D8Q 平台的材料赛道资讯仅依赖财联社、每日经济新闻、36氪三个通用财经源，缺乏材料领域专业站点的覆盖。十五五规划将新材料列为重点攻关方向，对应赛道（新材料、碳纤维等）需要更专业、更及时的垂直资讯支撑。需先对候选站点做技术验证（爬取可行性、数据质量、反爬难度），通过验证的站点纳入可用资讯源池，供后续材料赛道资讯采集使用。

## What Changes

- 新增"材料垂直站点技术验证"流程：对候选站点逐一测试爬取可行性，输出验证报告
- 为通过验证的站点开发专用爬虫模块，接入 data-agent 采集流水线
- 验证范围：国内站点（新材料在线、OFweek新材料、材料人/材料牛、中国复合材料工业协会、AZoM中文内容等）+ 国际站点（ScienceDaily Materials、Phys.org Materials、AZoM、Advanced Science News 等）
- 验证维度：页面结构可解析性、反爬机制强度、数据密度和质量、更新频率、是否有搜索/分类接口
- 通过验证的站点产出：可复用的爬虫模块 + 数据格式适配器，写入 financial_news 表

## Capabilities

### New Capabilities
- `material-site-validation`: 材料垂直站点爬取技术验证框架，定义验证标准、测试流程、通过/失败判定
- `material-crawler-modules`: 通过验证的站点爬虫模块集合，每个站点一个独立爬虫，统一输出格式

### Modified Capabilities

## Impact

- **data-agent**: 新增爬虫模块目录 `src/intelligent_data_agent/crawlers/material/`，需要扩展调度器支持新源
- **financial_news 表**: source 字段新增标识（如 `xincailiao`, `ofweek`, `sciencedaily` 等），subject 对应"新材料"/"碳纤维"赛道
- **依赖**: 现有 playwright 爬虫基础设施可复用；部分站点可能仅需 HTTP 请求 + HTML 解析（无需浏览器）
- **不影响现有功能**: 新增模块，不修改已有 cailianshe/nbd/36kr 爬虫
