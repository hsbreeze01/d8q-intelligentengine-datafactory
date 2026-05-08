# Delta Spec: 推荐页前端重构

## MODIFIED Requirements

### Requirement: 推荐页数据加载

推荐页 SHALL 使用三个 tab 展示不同维度的推荐数据：

1. **每日荐股**（默认）— 调用 `/api/proxy/recommendation/daily`，展示股票代码、名称、综合评分、技术面/趋势/基本面/成交量各维度分数、推荐理由、风险提示
2. **行业板块** — 调用 `/api/search/industries/summary`，展示行业板块涨跌排行；数据为空时显示"暂无数据"
3. **赛道热度** — 保留现有赛道热度展示逻辑

#### Scenario: 用户进入推荐页默认看到每日荐股

- **Given** 用户已登录并进入 `/recommend` 页面
- **When** 页面加载完成
- **Then** 默认选中"每日荐股" tab，自动调用 `/api/proxy/recommendation/daily` 加载数据

#### Scenario: 切换到行业板块 tab

- **Given** 用户在推荐页
- **When** 点击"行业板块" tab
- **Then** 调用 `/api/search/industries/summary` 获取行业板块数据并展示

#### Scenario: 行业板块数据为空时的降级

- **Given** 用户切换到"行业板块" tab
- **When** API 返回空数据或请求失败
- **Then** 页面显示"暂无数据"提示，不显示空白或报错

#### Scenario: 切换到赛道热度 tab

- **Given** 用户在推荐页
- **When** 点击"赛道热度" tab
- **Then** 显示现有赛道热度数据，行为与修改前完全一致

#### Scenario: 每日荐股数据展示

- **Given** compass 返回推荐数据包含评分和理由
- **When** 数据成功加载到"每日荐股" tab
- **Then** 每只推荐股票展示：股票代码、股票名称、综合评分（突出显示）、各维度分数条、推荐理由、风险提示
