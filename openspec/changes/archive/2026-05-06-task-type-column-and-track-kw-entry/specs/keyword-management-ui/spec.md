## MODIFIED Requirements

### Requirement: 赛道关键词管理入口
系统 SHALL 在赛道页面的赛道卡片上提供关键词管理入口，而非在采集任务列表中。

关键词管理模态框的交互逻辑不变：展示关键词标签列表、支持添加新关键词、支持删除已有关键词。

#### Scenario: 有关赛道任务不显示管理入口
- **WHEN** 采集任务列表中某个任务的 track_id 不为空
- **THEN** 该任务行只显示赛道 badge（名称+颜色），不显示"管理关键词"按钮

#### Scenario: 赛道页面提供管理入口
- **WHEN** 用户访问赛道页面（🔥 赛道）
- **THEN** 每个赛道卡片提供"管理关键词"操作入口，点击后弹出关键词管理模态框

### Requirement: 关键词列表展示
（无变更，保持原有 spec）

### Requirement: 添加新关键词
（无变更，保持原有 spec）

### Requirement: 删除关键词
（无变更，保持原有 spec）

### Requirement: Factory 代理路由补全
（无变更，保持原有 spec）
