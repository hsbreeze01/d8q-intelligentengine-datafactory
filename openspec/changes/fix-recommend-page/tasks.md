# Tasks: Fix Recommend Page

## Group 1: Frontend Recommend Page Rewrite

> **scope: frontend** — All tasks below require manual implementation.

- [x] **1.1** 重写推荐页标签按钮文案与默认视图
  - 将"行业精选"按钮文案改为"热门研报"
  - 将"概念龙头"按钮文案改为"赛道热度"
  - 确保默认激活第一个标签（热门研报）
  - scope: frontend — manual implementation

- [x] **1.2** 重写热门研报视图（`loadRecIndustry` → 热门研报）
  - 调用 `GET /api/stock/reports?keyword=&limit=10`
  - 渲染研报卡片网格：标题、机构、日期、分类标签
  - 处理空数据状态，显示"暂无研报数据"
  - 点击卡片跳转研报详情或原文链接
  - scope: frontend — manual implementation

- [x] **1.3** 重写赛道热度视图（`loadRecConcept` → 赛道热度）
  - 调用 `GET /api/proxy/tracks/heat/latest`
  - 渲染赛道列表：名称、热度分数、变化趋势箭头
  - 处理空数据状态
  - 点击赛道可跳转到赛道详情页
  - scope: frontend — manual implementation

- [x] **1.4** 重写主题搜索视图（`loadRecTheme` → 主题搜索优化）
  - 保留关键词输入框
  - 输入关键词后并行调用 `GET /api/stock/reports?keyword={kw}` 和 `GET /api/search/by-keyword?keyword={kw}`
  - 上方显示研报结果，下方显示匹配个股
  - 空结果时显示"未找到相关内容"
  - 添加防抖处理（300ms）
  - scope: frontend — manual implementation

## Group 2: Backend Verification

- [x] **2.1** 验证三个已有代理路由在推荐页场景下的可用性
  - 确认 `/api/stock/reports?keyword=&limit=10` 返回有效数据
  - 确认 `/api/proxy/tracks/heat/latest` 返回有效数据
  - 确认 `/api/search/by-keyword?keyword=新能源` 返回有效数据
  - 如有问题，修复路由或调整前端调用参数
