## ADDED Requirements

### Requirement: Dashboard shows personalized overview
Dashboard 页面 SHALL 默认展示当前用户订阅赛道的指标概览，而非全局数据。

#### Scenario: User with subscriptions sees personalized metrics
- **WHEN** lancer 登录后访问 Dashboard，订阅了 [人工智能, 碳纤维]
- **THEN** 指标卡片显示：今日资讯数（仅这2个赛道）、关注赛道数=2、热度异动（仅这2个赛道）；热度趋势图只展示这2个赛道；要闻列表只展示这2个赛道的资讯

#### Scenario: User without subscriptions sees full overview with guidance
- **WHEN** 新用户登录后访问 Dashboard，无订阅
- **THEN** 显示全部数据 + 顶部提示条"您尚未关注任何赛道，点击这里设置您的关注"

#### Scenario: Admin toggles to global view
- **WHEN** admin 在 Dashboard 页面点击"全局视图"按钮
- **THEN** 切换为显示所有赛道的完整数据

### Requirement: View mode toggle for admin
admin 角色 SHALL 在所有页面看到"全局视图 / 我的视图"切换控件。

#### Scenario: Toggle from personal to global
- **WHEN** admin 点击"全局视图"按钮
- **THEN** 所有页面数据切换为全量展示，按钮变为"我的视图"

#### Scenario: Toggle from global to personal
- **WHEN** admin 点击"我的视图"按钮
- **THEN** 所有页面数据切换为按 admin 订阅过滤

### Requirement: Subscription management UI
Factory SHALL 提供"我的关注"管理页面，支持用户订阅/取消赛道。

#### Scenario: User subscribes to a track
- **WHEN** 用户在"我的关注"页面点击某个赛道旁的"+ 关注"按钮
- **THEN** 赛道被加入订阅列表，按钮变为"已关注 ✓"，各页面数据即时更新

#### Scenario: User unsubscribes from a track
- **WHEN** 用户点击已关注赛道的"取消关注"按钮
- **THEN** 赛道从订阅列表移除，各页面数据即时更新

#### Scenario: New user sees track selection guidance
- **WHEN** 新用户首次登录
- **THEN** 弹出或显示赛道选择引导"请选择您关注的赛道"

### Requirement: Feed page defaults to subscribed tracks
资讯 Feed 页面 SHALL 默认只展示用户订阅赛道的资讯，但允许手动切换到全部赛道。

#### Scenario: Feed filtered by subscriptions
- **WHEN** lancer 访问 Feed 页面，订阅了 [人工智能]
- **THEN** 赛道筛选栏"人工智能"为默认选中，资讯列表只展示人工智能相关

#### Scenario: Feed manual switch to all tracks
- **WHEN** 用户在 Feed 页面点击"全部赛道"
- **THEN** 展示所有赛道的资讯

### Requirement: Stock page defaults to watchlist
个股页面 SHALL 默认展示用户自选股列表，搜索分析功能不受订阅限制。

#### Scenario: Stock page shows watchlist
- **WHEN** 用户访问个股页面
- **THEN** 自选股区域展示用户已添加的股票卡片

#### Scenario: Search any stock regardless of subscription
- **WHEN** 用户搜索未关注的股票代码
- **THEN** 正常返回分析结果，可加入自选
