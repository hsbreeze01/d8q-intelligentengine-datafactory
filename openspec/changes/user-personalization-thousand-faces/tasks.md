## 1. Agent 数据层 — 用户订阅/偏好 API

- [x] 1.1 Agent 启动时自动创建 `user_preferences` 表（CREATE TABLE IF NOT EXISTS），确保 `user_subscriptions`、`user_watchlist` 表存在
- [x] 1.2 新增 `/api/user/{user_id}/subscriptions` GET 端点 — 返回用户订阅的赛道列表（含 track name/color 等元信息）
- [x] 1.3 新增 `/api/user/subscribe` POST 端点 — 订阅赛道（插入 user_subscriptions）
- [x] 1.4 新增 `/api/user/subscribe/{user_id}/{track_id}` DELETE 端点 — 取消订阅
- [x] 1.5 新增 `/api/user/{user_id}/watchlist` GET 端点 — 返回用户自选股列表
- [x] 1.6 新增 `/api/user/watchlist` POST 端点 — 添加自选股（插入 user_watchlist）
- [x] 1.7 新增 `/api/user/{user_id}/watchlist/{stock_code}` DELETE 端点 — 删除自选股
- [x] 1.8 新增 `/api/user/{user_id}/preferences` GET/PUT 端点 — 用户偏好读写
- [x] 1.9 验证所有用户数据 API 端点功能正确（curl 测试）

## 2. Agent 数据过滤层

- [x] 2.1 `/api/news` 端点新增 `user_id` 可选参数 — 有值时按用户订阅赛道过滤 subject
- [x] 2.2 `/api/tracks` 端点新增 `user_id` 可选参数 — 有值时只返回用户订阅的赛道
- [x] 2.3 `/api/tracks/heat` 和 `/api/tracks/heat/latest` 新增 `user_id` 参数 — 过滤热度数据
- [x] 2.4 验证：无 user_id 时返回全量数据（向后兼容），有 user_id 时正确过滤

## 3. Factory 代理层 — 用户数据透传

- [x] 3.1 Factory 所有 `/api/proxy/*` 端点从 session 读取 username，透传为 user_id 参数给 Agent
- [x] 3.2 Factory `/api/news` 端点从 session 读取 username 透传给 Agent
- [x] 3.3 Factory `/api/stock/*` 端点 watchlist 操作改为调 Agent API（不再本地管理）
- [x] 3.4 Factory 新增 `/api/user/subscribe`、`/api/user/watchlist` 等代理端点
- [x] 3.5 admin 角色支持 `view=all` 参数，透传时跳过 user_id 过滤
- [x] 3.6 验证：viewer 登录后 API 返回过滤数据，admin 可切换全局视图

## 4. 前端 — 用户偏好管理页面

- [x] 4.1 侧边栏新增"⭐ 我的关注"页面（policy 移到研报后不变，在设置分隔线上方新增）
- [x] 4.2 "我的关注"页面：展示所有赛道列表，已订阅的显示"已关注 ✓"，未订阅的显示"+ 关注"按钮
- [x] 4.3 "我的关注"页面：展示自选股列表，支持搜索添加和删除
- [x] 4.4 订阅/取消操作即时生效，调用 Factory 代理 API → Agent API
- [x] 4.5 新用户首次登录显示引导提示条"请选择您关注的赛道"

## 5. 前端 — 个性化 Dashboard

- [x] 5.1 `loadDashboard` 从 session 获取 username，API 请求带 user_id 参数
- [x] 5.2 Dashboard 指标卡片、热度图表、要闻列表全部基于订阅过滤
- [x] 5.3 admin 角色在 Dashboard 顶部显示"全局视图 / 我的视图"切换按钮
- [x] 5.4 无订阅用户显示全量数据 + 引导提示条

## 6. 前端 — 各页面接入用户过滤

- [x] 6.1 `loadFeed` 默认只展示用户订阅赛道的资讯，赛道筛选栏预选中订阅赛道
- [x] 6.2 `loadPolicy` 默认只分析用户订阅赛道的政策资讯
- [x] 6.3 `loadReport` 赛道筛选栏只展示用户订阅的赛道
- [x] 6.4 `loadStock` 自选股从 Agent user_watchlist API 加载
- [x] 6.5 admin "全局视图/我的视图"切换控件在所有页面持久生效（存入 localStorage）

## 7. 验收测试

- [x] 7.1 viewer 用户登录后只能看到自己订阅的赛道内容
- [x] 7.2 admin 切换全局视图后可看到所有数据
- [x] 7.3 无订阅新用户看到全量数据 + 引导提示
- [x] 7.4 服务间内部调用不受用户过滤影响
- [x] 7.5 订阅/取消操作后页面刷新数据正确
- [ ] 7.6 所有改动提交代码并推送到远端
