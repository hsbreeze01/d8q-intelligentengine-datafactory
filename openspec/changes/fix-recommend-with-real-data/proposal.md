# Proposal: 修复推荐页 — 接入真实股票推荐数据

## 背景

当前 factory 推荐页（/recommend）存在**概念混淆**问题：

1. **赛道热度（Tracks Heat）!= 股票推荐**：赛道是 compass/dataagent 的信息聚合主题（人工智能、具身智能等），用于新闻追踪。推荐页不应显示赛道热度作为"推荐"。
2. **行业/概念板块（Industries/Concepts）数据为空**：stockshark 的 `/api/search/industries` 和 `/api/search/concepts` 通过 akshare 实时调用东方财富 API，但服务器网络不通导致返回空。
3. **compass 量化推荐引擎未接入**：compass 有完整的 RecommendationService（技术面40% + 趋势25% + 基本面20% + 成交量15%评分），API 路由已存在但从未被 factory 使用。

## 问题清单

### P0: 推荐页无真实股票数据
- compass `/api/recommendation/daily` 可返回量化评分的股票推荐，但 factory 未接入
- factory 推荐页当前显示赛道热度/研报/主题搜索，不是用户期望的"股票推荐"

### P1: stockshark 行业/概念数据为空
- SearchEngine 的 get_all_industries 和 get_all_concepts 依赖 akshare 实时调用东方财富 API
- 服务器无法连通东方财富 API 导致数据为空
- 需要本地缓存机制或数据预加载

### P2: compass recommendation 数据依赖
- daily_recommendation 表已创建
- dic_stock 表有结构但数据为空，推荐引擎无法运行
- compass 有 DailyAnalysisTask 调度器来同步股票数据

## 解决方案

### Task 1: factory 接入 compass 推荐数据 [scope: backend]

**文件**: app.py

在 factory 中新增 compass 推荐代理路由：
- GET /api/proxy/recommendation/daily - 代理到 http://localhost:8087/api/recommendation/daily
- GET /api/proxy/recommendation/generate - POST 代理到 http://localhost:8087/api/recommendation/generate（管理员触发推荐计算）

配置常量：COMPASS_API = "http://localhost:8087"

新增 compass_request 代理函数（类似现有的 shark_request）。

### Task 2: stockshark 行业/概念数据本地缓存 [scope: backend]

**文件**: stockshark/analysis/search_engine.py 和 stockshark/data/akshare_data.py

改造 get_all_industries 和 get_all_concepts：
- 首先查 MySQL 表 stock_analysis_system 中是否已有缓存数据
- 如果有缓存且未过期（小于24h），直接返回
- 如果无缓存或已过期，尝试 akshare 实时调用
- 如果 akshare 也失败，返回缓存数据（即使过期）

备选方案（如果上述不可行）：
- 在 stockshark 中新增本地 JSON 缓存到 /var/cache/stockshark/ 目录，24h TTL
- industries.json 和 concepts.json

### Task 3: factory 推荐页前端重构 [scope: frontend]

**文件**: templates/index.html

推荐页 loadRecommend 重构为三个 tab：
1. **每日荐股** - 调 /api/proxy/recommendation/daily，显示股票代码、名称、综合评分、各维度分数、推荐理由、风险提示
2. **行业板块** - 调 /api/search/industries/summary，显示行业板块涨跌排行（如果数据为空显示"暂无数据"）
3. **赛道热度** - 保留现有赛道热度展示（从推荐页移到此处作为补充维度）

默认加载"每日荐股" tab。

### Task 4: 测试 [scope: backend]

**文件**: tests/test_recommend_routes.py

新增测试：
- GET /api/proxy/recommendation/daily 返回 200
- 代理正确转发到 compass
- compass 不可用时优雅降级

## 技术约束

- stockshark 运行在端口 5000（gunicorn via systemd d8q-stockshark.service）
- compass 运行在端口 8087（gunicorn，d8q-compass.service 当前 dead 但有手动启动的进程）
- factory 运行在端口 8088（gunicorn via systemd d8q-factory.service）
- MySQL: stock_analysis_system 数据库，root/password@localhost:3306
- 已有代理函数 shark_request 可参考新增 compass_request
- factory 已有 COMPASS 相关路由：/api/proxy/tracks/* 代理到 dataagent（port 8000）
- 注意区分 compass（8087）和 dataagent（8000）是不同服务

## 验收标准

1. GET /api/proxy/recommendation/daily 返回 200，数据来自 compass
2. 推荐页"每日荐股" tab 显示评分、股票名、推荐理由
3. "行业板块" tab 有数据时显示，无数据时优雅提示
4. 现有赛道热度功能不受影响
5. 所有新增测试通过
