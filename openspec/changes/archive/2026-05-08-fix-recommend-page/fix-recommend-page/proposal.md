# Proposal: Fix Recommend Page - Use Available Data Sources

## Summary
推荐页当前显示空白，因为依赖的 stockshark industries/concepts/sectors 接口返回空数据。需要改为使用 stockshark 实际有数据的接口来驱动推荐内容。

## Motivation
推荐页的三个视图（行业精选/概念龙头/主题投资）分别调用 sectors、concepts、by-theme 接口，底层依赖的 stockshark 数据库中 industry 和 concept 表为空。需要改用有数据的接口。

## Root Cause Analysis
1. sectors 接口需要 symbol 参数，不支持列表查询
2. industries 接口 - stockshark get_all_industries() 返回空，数据库无行业数据
3. concepts 接口 - stockshark get_all_concepts() 返回空，数据库无概念数据

## Available Data Sources (stockshark has data)
1. /api/report/search?keyword=xxx and limit=20 - 研报搜索，有数据
2. /api/analysis/stock/basic?symbol=xxx - 个股基础信息，包含 industry 字段
3. factory 自有的 /api/proxy/tracks - 赛道数据，有数据
4. factory 自有的 /api/proxy/tracks/heat/latest - 赛道热度，有数据
5. /api/watchlist - 用户自选股

## Expected Behavior
重写推荐页的三个视图，改用有数据的数据源：

### View 1: 热门研报 (替换行业精选)
- 调用 /api/stock/reports?keyword= and limit=10 获取最新研报
- 展示研报卡片：标题、机构、日期、分类标签
- 点击可查看研报详情或跳转原文

### View 2: 赛道热度 (替换概念龙头)
- 调用 /api/proxy/tracks/heat/latest 获取赛道热度数据
- 展示赛道卡片：名称、热度分数、变化趋势
- 复用 factory 已有的赛道数据

### View 3: 主题搜索 (保留，优化体验)
- 输入关键词后调用 /api/stock/reports?keyword=xxx 搜索相关研报
- 展示搜索结果列表
- 同时可调用 /api/search/by-keyword?keyword=xxx 搜索匹配的个股

### 后端改动
- 确认 /api/stock/reports 代理路由已存在且可用
- 无需新增路由，所有需要的数据源已就绪

### 前端改动 (scope: frontend - 由人工完成)
- 重写 loadRecommend/loadRecIndustry/loadRecConcept/loadRecTheme 函数
- 修改按钮文案：行业精选改为热门研报，概念龙头改为赛道热度
