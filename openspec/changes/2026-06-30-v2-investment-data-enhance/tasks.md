# 任务清单：投融资数据增强(热力图+机构追踪)

## 阶段一：Agent端API开发 (预计2天)

### Task 1.1: 热力图API - GET /api/itjuzi/heatmap
- [ ] 在 `agent/routers/itjuzi.py` 新增路由
- [ ] 实现参数校验(months: 1-24, metric: count/amount)
- [ ] 实现热力图矩阵查询(月×行业Top10)
- [ ] 实现趋势数据聚合(按月event_count + total_amount)
- [ ] 实现轮次分布聚合(按round分组)
- [ ] 组装统一响应格式
- [ ] 添加Redis缓存(5分钟TTL)
- [ ] 单元测试

### Task 1.2: 机构排行API - GET /api/itjuzi/investors/top
- [ ] 在 `agent/routers/itjuzi.py` 新增路由
- [ ] 实现参数校验(days: 1-365, limit: 1-100, industry可选)
- [ ] 实现investors JSON解析与聚合逻辑
- [ ] 按deal_count排序取TopN
- [ ] 补充recent_deals(最近5条)
- [ ] 计算lead_count、avg_amount、industries、rounds分布
- [ ] 添加Redis缓存(10分钟TTL)
- [ ] 单元测试
- [ ] 边界测试：investors为空/null/格式异常的容错

### Task 1.3: Agent端集成测试
- [ ] 测试heatmap接口在真实数据上的性能(目标<500ms)
- [ ] 测试investors/top在大数据量下的性能
- [ ] 验证缓存命中/失效逻辑
- [ ] 验证参数边界值处理

---

## 阶段二：Factory端开发 (预计2天)

### Task 2.1: 数据库变更
- [ ] 编写followed_investors建表DDL
- [ ] 在Factory数据库执行建表
- [ ] 验证索引和约束生效

### Task 2.2: 代理路由 - heatmap & investors/top
- [ ] 在 `routes/investment.js` 新增 GET /api/investment/heatmap
- [ ] 新增 GET /api/investment/investors/top
- [ ] 透传query参数到Agent
- [ ] investors/top响应中附加is_followed标记
- [ ] 错误处理(Agent不可用时返回502)

### Task 2.3: 关注机构CRUD
- [ ] POST /api/investment/follow (创建关注)
  - 参数校验(investor_name非空，<=200字符)
  - 鉴权检查(req.user.id)
  - UNIQUE冲突处理(409)
- [ ] DELETE /api/investment/follow/:investor_name (取消关注)
  - 幂等处理
- [ ] GET /api/investment/follow (获取关注列表)
- [ ] 单元测试

### Task 2.4: 预警联动
- [ ] 实现 POST /api/investment/follow/check-alerts 内部接口
- [ ] 查询所有被关注机构(DISTINCT)
- [ ] 调用Agent获取最近1小时新事件
- [ ] 匹配investors字段包含关注机构名的事件
- [ ] 为对应用户写入alerts表
- [ ] WebSocket推送通知
- [ ] 注册Cron定时任务(每小时执行)
- [ ] 添加去重逻辑(同一事件不重复告警)

---

## 阶段三：前端开发 (预计3天)

### Task 3.1: Tab结构改造
- [ ] 改造loadInvestment()函数，输出Tab导航
- [ ] 实现switchInvestmentTab()切换逻辑
- [ ] 事件列表Tab保持现有功能不变
- [ ] Tab状态记忆(切换回来不重新加载)
- [ ] 添加Tab样式(active状态高亮)

### Task 3.2: 热力分析Tab
- [ ] 确认ECharts引入(CDN或本地)
- [ ] 实现月份筛选按钮组(3/6/12月)
- [ ] 调用 /api/investment/heatmap 获取数据
- [ ] 渲染ECharts热力图(行业×月份)
  - 配置visualMap色阶
  - tooltip显示具体数值
  - 响应式适配容器宽度
- [ ] 渲染趋势折线图(双Y轴)
  - 左轴事件数，右轴金额(亿)
  - 面积填充区分
- [ ] 渲染轮次饼图(环形图)
  - 显示百分比
  - legend居右
- [ ] 无数据时显示空状态提示
- [ ] 加载状态(loading动画)

### Task 3.3: 机构追踪Tab
- [ ] 实现筛选栏(天数按钮组 + 行业下拉)
- [ ] 调用 /api/investment/investors/top 获取数据
- [ ] 渲染排行榜表格
  - 序号、机构名、出手次数、领投次数、总金额、关注按钮
  - 支持列头排序切换
- [ ] 实现行展开/折叠(recent_deals明细)
- [ ] 实现关注/取消关注按钮
  - 调用follow/unfollow API
  - 按钮状态即时切换
  - toast反馈
- [ ] 加载状态 + 空状态处理

### Task 3.4: 样式与响应式
- [ ] Tab导航样式
- [ ] 热力图容器自适应
- [ ] 排行榜表格样式(hover、展开动画)
- [ ] 关注按钮样式(星标图标)
- [ ] 移动端适配(表格横向滚动)

---

## 阶段四：联调与测试 (预计1天)

### Task 4.1: 端到端联调
- [ ] Agent heatmap → Factory代理 → 前端热力图渲染
- [ ] Agent investors/top → Factory代理(+is_followed) → 前端排行榜
- [ ] 关注操作 → 数据库持久化 → 刷新后状态保持
- [ ] 预警触发 → alerts写入 → WebSocket推送 → 前端通知

### Task 4.2: 性能验证
- [ ] 热力图API响应时间 < 500ms (缓存后 < 50ms)
- [ ] 机构排行API响应时间 < 1s (缓存后 < 100ms)
- [ ] 前端ECharts渲染流畅(FPS > 30)
- [ ] 大数据量下investors JSON解析不OOM

### Task 4.3: 边界与异常测试
- [ ] Agent不可用时Factory返回友好错误
- [ ] 无数据月份热力图正确显示0值
- [ ] investors JSON格式异常容错
- [ ] 并发关注/取消操作幂等性
- [ ] 预警去重(同一事件不重复产生)

### Task 4.4: 部署上线
- [ ] Agent端代码部署
- [ ] Factory端代码部署 + 数据库DDL执行
- [ ] 前端静态资源更新
- [ ] Cron任务注册验证
- [ ] 线上冒烟测试

---

## 依赖项

| 依赖 | 状态 | 说明 |
|------|------|------|
| itjuzi_investevent表 | ✅ 已有 | 含investors JSON字段 |
| Agent /api/itjuzi/events | ✅ 已有 | 参考现有路由结构 |
| Factory /api/investment/* | ✅ 已有 | 已有代理模式 |
| alerts表 + WebSocket | ✅ 已有 | 预警中心基础设施 |
| ECharts | ⚠️ 需确认 | 前端是否已引入 |
| Redis | ✅ 已有 | Agent端缓存 |

## 验收标准

1. 热力分析Tab可视化数据准确，热力图/趋势图/饼图正常渲染
2. 机构排行数据与原始数据一致(抽样验证)
3. 关注/取消操作正常，刷新后状态保持
4. 关注机构新投资时，1小时内收到预警通知
5. 所有API响应时间满足性能指标
6. 无数据/异常场景友好提示，不出现白屏或崩溃
