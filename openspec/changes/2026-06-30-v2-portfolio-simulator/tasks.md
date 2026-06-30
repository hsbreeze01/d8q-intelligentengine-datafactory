# 任务拆解 - 虚拟组合模块

## Phase 1: 数据层（Day 1-2）

### Task 1.1 - 创建数据库表
- [ ] 在 Factory 启动逻辑中添加 portfolio 相关表的 DDL
- [ ] 创建 portfolios 表（含 cash 字段）
- [ ] 创建 positions 表（含唯一约束 portfolio_id+stock_code）
- [ ] 创建 trades 表
- [ ] 创建 net_value_history 表
- [ ] 添加索引
- [ ] 启用 PRAGMA foreign_keys = ON

### Task 1.2 - 数据访问层
- [ ] 封装 portfolio_db.py 模块
- [ ] CRUD: create_portfolio / get_portfolio / list_portfolios / update_portfolio / delete_portfolio
- [ ] Position: get_positions / upsert_position / delete_position
- [ ] Trade: insert_trade / list_trades
- [ ] NetValue: insert_net_value / get_net_value_series

---

## Phase 2: 后端 API（Day 2-4）

### Task 2.1 - 组合 CRUD API
- [ ] GET /api/portfolios — 获取当前用户所有组合（含汇总数据）
- [ ] POST /api/portfolios — 创建组合（校验 name/initial_capital）
- [ ] GET /api/portfolios/{id} — 组合详情（含持仓列表）
- [ ] PUT /api/portfolios/{id} — 修改组合名称
- [ ] DELETE /api/portfolios/{id} — 删除组合（级联删除）
- [ ] 所有接口校验 session username 权限

### Task 2.2 - 模拟交易 API
- [ ] POST /api/portfolios/{id}/trade — 执行买入/卖出
- [ ] 买入逻辑：校验现金 → 扣减现金 → 更新/创建持仓（加权平均成本）
- [ ] 卖出逻辑：校验持仓 → 增加现金 → 减少持仓（清仓则删除记录）
- [ ] GET /api/portfolios/{id}/trades — 分页查询交易记录
- [ ] 参数校验：stock_code 6位数字、quantity > 0、direction 枚举

### Task 2.3 - 绩效 API
- [ ] GET /api/portfolios/{id}/performance — 返回绩效摘要 + 净值序列 + 基准序列
- [ ] 收益率计算: (总市值 + 现金 - 初始资金) / 初始资金
- [ ] 最大回撤计算
- [ ] 夏普比率计算（年化，无风险利率3%）
- [ ] 基准数据：从 Shark 获取 sh000300 历史净值归一化

### Task 2.4 - 现价刷新 API
- [ ] POST /api/portfolios/{id}/refresh-price — 手动刷新
- [ ] 调用 Shark GET /api/stock/quote?symbol={code}
- [ ] 批量更新 positions.current_price
- [ ] 返回更新数量和失败列表

---

## Phase 3: 定时任务（Day 4-5）

### Task 3.1 - 每日现价更新
- [ ] 使用 APScheduler 注册定时任务
- [ ] 触发时间：周一至周五 15:35
- [ ] 查询所有 positions 表的 stock_code（去重）
- [ ] 批量调用 Shark 获取最新价
- [ ] 更新 positions.current_price 和 updated_at
- [ ] 失败重试 3 次，间隔 5 秒

### Task 3.2 - 每日净值快照
- [ ] 在现价更新完成后计算各组合净值
- [ ] net_value = total_assets / initial_capital
- [ ] 写入 net_value_history 表
- [ ] 跳过非交易日（简化：跳过周六日）

---

## Phase 4: 前端页面（Day 5-8）

### Task 4.1 - PAGES 注册与路由
- [ ] PAGES 数组新增 { id: 'portfolio', title: '虚拟组合', icon: '📊' }
- [ ] loadPage('portfolio') 加载组合模块
- [ ] 侧边栏菜单渲染

### Task 4.2 - 组合列表页
- [ ] 卡片式布局展示所有组合
- [ ] 每卡片显示：名称、总资产、收益率（红涨绿跌）、持仓数、创建日期
- [ ] 「+新建组合」按钮 → 弹窗表单（名称 + 初始资金）
- [ ] 点击卡片 → 进入详情视图
- [ ] 卡片右上角删除按钮（二次确认）

### Task 4.3 - 组合详情页
- [ ] 顶部摘要栏：总资产/现金/收益率/最大回撤/夏普比率
- [ ] Tab 切换：持仓 | 交易记录 | 绩效看板
- [ ] 持仓 Tab：表格展示（代码/名称/数量/成本/现价/盈亏/盈亏%），盈亏着色
- [ ] 交易记录 Tab：表格展示，分页加载
- [ ] 绩效看板 Tab：ECharts 净值曲线

### Task 4.4 - 交易表单
- [ ] 组合详情页底部「快速交易」区域
- [ ] 表单字段：股票代码、股票名称、方向（买入/卖出切换）、价格、数量、备注
- [ ] 输入股票代码后自动获取当前价填充 price 字段
- [ ] 实时计算「预计金额」
- [ ] 提交后刷新持仓列表

### Task 4.5 - ECharts 绩效看板
- [ ] 引入 ECharts CDN
- [ ] 折线图：X轴日期，Y轴净值
- [ ] 双线：组合净值（蓝色）+ 沪深300基准（灰色虚线）
- [ ] tooltip 显示具体数值和差异
- [ ] 响应式自适应容器宽度

---

## Phase 5: 联调与测试（Day 8-10）

### Task 5.1 - 端到端联调
- [ ] 创建组合 → 执行多笔交易 → 查看持仓变化
- [ ] 验证现金扣减和增加逻辑
- [ ] 验证加权平均成本计算
- [ ] 验证清仓后持仓删除
- [ ] 验证定时任务现价更新

### Task 5.2 - 边界情况
- [ ] 现金不足买入 → 返回错误
- [ ] 持仓不足卖出 → 返回错误
- [ ] 删除组合 → 级联删除确认
- [ ] Shark 接口超时 → 降级处理
- [ ] 非本人组合访问 → 403

### Task 5.3 - 性能验证
- [ ] 100个组合 × 20个持仓场景下的列表加载
- [ ] 净值序列 365 天数据的图表渲染
- [ ] 定时任务批量更新 200+ 持仓的耗时

---

## 验收标准

1. ✅ 用户可创建/编辑/删除虚拟组合
2. ✅ 可执行模拟买入卖出，持仓和现金正确更新
3. ✅ 收益率、最大回撤、夏普比率计算正确
4. ✅ 每日自动刷新持仓现价并记录净值
5. ✅ ECharts 净值曲线正确展示，叠加沪深300基准
6. ✅ 多用户数据隔离，仅能操作自己的组合
7. ✅ 所有 API 错误码和响应格式符合 spec 定义
