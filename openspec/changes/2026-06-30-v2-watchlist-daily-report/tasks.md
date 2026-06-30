# 任务拆解 - 自选股日报与评分变化

## 里程碑总览

| 阶段 | 内容 | 预估工时 | 依赖 |
|------|------|---------|------|
| M1 | 数据层：score_history 表 + 定时任务 | 2h | 无 |
| M2 | API 层：daily-report + score-history | 2h | M1 |
| M3 | 前端：表格改造 + sparkline | 3h | M2 |
| M4 | 前端：归因弹窗 + 交互 | 2h | M3 |
| M5 | 联调测试 + 修复 | 1h | M4 |

**总预估**：10h

---

## M1 - 数据层

### Task 1.1 创建 score_history 表
- [ ] 在 `financial_news.db` 中执行建表 SQL
- [ ] 创建 `UNIQUE(stock_code, date)` 约束
- [ ] 创建 `idx_score_history_code_date` 和 `idx_score_history_date` 索引
- [ ] 验证表结构

### Task 1.2 实现定时任务
- [ ] 安装/确认 APScheduler 依赖
- [ ] 在 `app.py` 中初始化 BackgroundScheduler
- [ ] 实现 `daily_score_calculation()` 函数
  - 获取所有自选股（去重）
  - 逐只调用 `/api/stock/comprehensive`
  - INSERT OR REPLACE 写入 score_history
  - 异常处理：单只失败不影响整体
- [ ] 配置 CronTrigger(hour=8, minute=30)
- [ ] 实现 `derive_signal()` 信号派生逻辑
- [ ] 添加日志记录（成功/失败计数）

### Task 1.3 补算接口
- [ ] 实现 `POST /api/watchlist/recalculate`
- [ ] 支持指定 date 和可选 stock_codes
- [ ] 手动触发一次计算，验证数据写入

---

## M2 - API 层

### Task 2.1 日报接口
- [ ] 实现 `GET /api/watchlist/daily-report`
- [ ] 查询 today + yesterday 的 score_history
- [ ] 计算 change 和 change_pct
- [ ] 组装 dimensions 各维度变化
- [ ] 附带最近7天 sparkline 数据
- [ ] 实现 sort 参数（默认 change_desc）
- [ ] 生成 summary 统计

### Task 2.2 历史评分接口
- [ ] 实现 `GET /api/watchlist/{code}/score-history`
- [ ] 支持 days 参数（默认7，最大90）
- [ ] 返回历史记录 + trend 统计
- [ ] 错误处理（404 无数据）

### Task 2.3 API 验证
- [ ] 无评分数据时返回合理默认值
- [ ] 新加入自选股（无历史）的处理
- [ ] 响应时间验证 < 500ms

---

## M3 - 前端表格改造

### Task 3.1 HTML 结构
- [ ] 将自选股 grid 替换为 table 结构
- [ ] 添加表头：代码/名称/今日分/昨日分/变化/信号/风险/7日走势/操作
- [ ] 添加日报 header（日期 + 摘要统计）

### Task 3.2 数据加载
- [ ] 修改 `loadWatchlist()` 调用 daily-report API
- [ ] 实现 `renderDailyReport()` 渲染函数
- [ ] 实现排序切换交互
- [ ] 信号/风险标签样式渲染

### Task 3.3 Sparkline
- [ ] 实现 `renderSparkline()` 使用 ECharts mini chart
- [ ] 配置：120×30px，无轴线，平滑曲线
- [ ] 颜色逻辑：上涨红色，下跌绿色
- [ ] 确保多图表实例不冲突

### Task 3.4 样式
- [ ] 编写 table 基础样式
- [ ] 变化值颜色（红涨绿跌灰平）
- [ ] 信号标签样式（5种颜色）
- [ ] 风险等级颜色
- [ ] 行 hover 效果
- [ ] 响应式适配

---

## M4 - 归因弹窗

### Task 4.1 弹窗结构
- [ ] 添加归因 modal HTML
- [ ] 实现打开/关闭交互
- [ ] 点击行触发 `showAttribution(stock)`

### Task 4.2 归因图表
- [ ] 实现 `renderAttributionChart()` 柱状图
- [ ] 4维度对比（昨日 vs 今日 vs 变化）
- [ ] 标注"主要变化维度"（变化绝对值最大的）
- [ ] 颜色编码正负变化

### Task 4.3 交互优化
- [ ] 点击背景关闭弹窗
- [ ] ESC 键关闭
- [ ] 移动端适配

---

## M5 - 联调测试

### Task 5.1 端到端验证
- [ ] 手动触发 recalculate 生成测试数据
- [ ] 验证 daily-report API 返回正确
- [ ] 验证前端表格渲染完整
- [ ] 验证 sparkline 显示正确
- [ ] 验证归因弹窗数据正确

### Task 5.2 边界情况
- [ ] 空自选股列表显示
- [ ] 新加入股票（仅1天数据）
- [ ] 全部股票无变化
- [ ] 综合分析 API 部分失败

### Task 5.3 性能验证
- [ ] 30只自选股日报 API < 500ms
- [ ] 页面首次加载 < 2s
- [ ] Sparkline 批量渲染无卡顿

---

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `app.py` | 修改 | 新增定时任务 + 3个API路由 |
| `financial_news.db` | 修改 | 新增 score_history 表 |
| `templates/index.html` | 修改 | 自选股区域改为增强 table |
| `static/css/style.css` | 修改 | 新增表格/信号/sparkline 样式 |
| `static/js/main.js` | 修改 | 新增日报渲染/sparkline/归因逻辑 |

---

## 风险项

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| comprehensive API 不返回子维度评分 | 归因无法展示 | 确认 API 返回字段，必要时改造 comprehensive |
| APScheduler 在 Flask 多进程下重复执行 | 重复计算 | 使用 UNIQUE 约束 + 单进程模式 |
| 历史数据空白（首次上线） | sparkline 无数据 | 上线后手动补算近7天 |
| ECharts 在 table 单元格内渲染异常 | sparkline 不显示 | 备选方案：SVG path 手绘 |
