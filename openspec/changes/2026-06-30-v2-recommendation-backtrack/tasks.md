# Tasks: 推荐回溯验证

## 1. Shark端 — 数据层

- [ ] 1.1 创建 recommendation_results 表 DDL (1 file: Shark app.py 或 models)
- [ ] 1.2 修改每日推荐流程，推荐生成后自动写入 recommendation_results (1 file: Shark 推荐模块)
- [ ] 1.3 实现 backfill_recommendation_returns 回填函数 (1 file: Shark 新模块 `rec_backfill.py`)
- [ ] 1.4 注册每日定时任务(15:30执行回填) (1 file: Shark scheduler)
- [ ] 1.5 编写一次性历史补填脚本(回溯已有推荐的T+N数据) (1 file: `scripts/backfill_history.py`)

## 2. Shark端 — API

- [ ] 2.1 实现 GET /api/recommendation/history (分页+天数筛选) (1 file: Shark app.py)
- [ ] 2.2 实现 GET /api/recommendation/stats (胜率+维度拆解+累计曲线) (1 file: Shark app.py)
- [ ] 2.3 API响应格式验证和错误处理 (1 file: Shark app.py)

## 3. Factory端 — 代理

- [ ] 3.1 新增 GET /api/proxy/recommendation/history 代理路由 (1 file: `app.py`)
- [ ] 3.2 新增 GET /api/proxy/recommendation/stats 代理路由 (1 file: `app.py`)

## 4. 前端 — 历史回溯Tab

- [ ] 4.1 修改 loadRecommend 添加第4个Tab按钮「历史回溯」(1 file: `templates/index.html`)
- [ ] 4.2 实现 loadRecBacktrack() 函数 — 调用API获取数据 (1 file: `templates/index.html`)
- [ ] 4.3 渲染顶部统计卡(胜率/超额收益/总数/最佳) (1 file: `templates/index.html`)
- [ ] 4.4 渲染ECharts累计收益曲线(推荐组合 vs 沪深300) (1 file: `templates/index.html`)
- [ ] 4.5 渲染维度胜率对比(技术/趋势/基本面/量能) (1 file: `templates/index.html`)
- [ ] 4.6 渲染历史推荐表格(颜色标记+胜负标记+分页) (1 file: `templates/index.html`)
- [ ] 4.7 实现日期范围筛选交互 (1 file: `templates/index.html`)

## 5. 集成与测试

- [ ] 5.1 运行历史补填脚本，验证数据完整性
- [ ] 5.2 等待1天后验证T+1自动回填
- [ ] 5.3 前端展示验证（数据对齐、图表正确）
- [ ] 5.4 冷启动场景验证（数据不足时降级展示）

## 文件变更清单

| 文件 | 位置 | 变更类型 |
|------|------|----------|
| app.py (或数据模型) | Shark (49服务器) | 修改: 新增表+2个API |
| rec_backfill.py | Shark | 新增: 回填逻辑 |
| scheduler相关 | Shark | 修改: 注册每日回填job |
| scripts/backfill_history.py | Shark | 新增: 一次性历史补填 |
| app.py | Factory (47服务器) | 修改: 新增2个代理路由 |
| templates/index.html | Factory | 修改: 推荐页新增Tab |

## 依赖项
- Shark需要有历史日K数据(已有)
- 需要知道交易日历(排除非交易日)
- 沪深300指数数据(Shark已有或需新增采集)

## 预估工期: 4天
- Shark端数据层+API: 2天
- Factory代理+前端: 1.5天
- 联调测试: 0.5天
