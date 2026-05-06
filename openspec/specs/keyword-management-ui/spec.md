## ADDED Requirements

### Requirement: 赛道关键词管理入口
系统 SHALL 在赛道页面的赛道卡片上提供关键词管理入口，点击后弹出该赛道的关键词管理模态框。仅 admin 角色可见该入口。

#### Scenario: 赛道页面提供管理入口
- **WHEN** 用户访问赛道页面（🔥 赛道）且角色为 admin
- **THEN** 每个赛道卡片提供"🔑 管理关键词"操作入口，点击后弹出关键词管理模态框

#### Scenario: 有关赛道任务不显示管理入口
- **WHEN** 采集任务列表中某个任务的 track_id 不为空
- **THEN** 该任务行只显示赛道 badge（名称+颜色），不显示"管理关键词"按钮

#### Scenario: 非 admin 用户不可见
- **WHEN** 用户角色不是 admin
- **THEN** 赛道卡片不显示"管理关键词"入口，API 调用返回 403

### Requirement: 关键词列表展示
系统 SHALL 在关键词管理面板中以标签（tag）形式展示该赛道的所有已有关键词，每个标签旁边有删除按钮。

#### Scenario: 展示已有关键词
- **WHEN** 用户打开某赛道的关键词管理面板
- **THEN** 系统调用 `GET /api/proxy/tracks/{id}/keywords` 获取关键词列表，以标签形式逐个展示

#### Scenario: 无关键词时的空状态
- **WHEN** 赛道没有任何关键词
- **THEN** 面板显示"暂无关键词，请添加"提示文本

### Requirement: 添加新关键词
系统 SHALL 允许用户在关键词管理面板中输入新关键词并添加到赛道。

#### Scenario: 成功添加关键词
- **WHEN** 用户在输入框中输入非空文本并点击"添加"
- **THEN** 系统调用 `POST /api/proxy/tracks/{id}/keywords` 提交新关键词，成功后刷新面板中的关键词列表

#### Scenario: 添加空关键词被拒绝
- **WHEN** 用户在输入框中输入空白文本并点击"添加"
- **THEN** 系统显示"关键词不能为空"的提示，不发送请求

#### Scenario: 添加重复关键词
- **WHEN** 用户添加已存在的关键词
- **THEN** 后端返回错误，前端显示"关键词已存在"提示

### Requirement: 删除关键词
系统 SHALL 允许用户从赛道中删除已有关键词。

#### Scenario: 成功删除关键词
- **WHEN** 用户点击某个关键词标签上的删除按钮
- **THEN** 系统调用 `DELETE /api/proxy/tracks/{id}/keywords/{keyword}`，成功后从面板中移除该标签

### Requirement: Factory 代理路由补全
Factory `app.py` SHALL 提供关键词的写入操作代理路由，仅 admin 角色可调用。

#### Scenario: POST 代理路由转发
- **WHEN** admin 用户调用 `POST /api/proxy/tracks/{id}/keywords`
- **THEN** Factory 将请求体原样转发到 data-agent 的 `POST http://127.0.0.1:8000/api/tracks/{id}/keywords`，返回 data-agent 的响应

#### Scenario: DELETE 代理路由转发
- **WHEN** admin 用户调用 `DELETE /api/proxy/tracks/{id}/keywords/{keyword}`
- **THEN** Factory 将请求转发到 data-agent 的 `DELETE http://127.0.0.1:8000/api/tracks/{id}/keywords/{keyword}`，返回 data-agent 的响应

#### Scenario: 非 admin 被拒绝
- **WHEN** 非 admin 用户调用 POST 或 DELETE 代理路由
- **THEN** 返回 403 错误
