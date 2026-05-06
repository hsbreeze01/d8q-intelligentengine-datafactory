## ADDED Requirements

### Requirement: 采集任务类型列
系统 SHALL 在采集任务表格中增加"类型"列，用 badge 标注每个任务是"赛道采集"还是"自定义采集"。

#### Scenario: 赛道任务显示类型 badge
- **WHEN** 采集任务的 track_id 不为空（赛道任务）
- **THEN** 类型列显示蓝色 badge "赛道采集"，并附带赛道名称

#### Scenario: 自定义任务显示类型 badge
- **WHEN** 采集任务没有 track_id（自定义任务）
- **THEN** 类型列显示灰色 badge "自定义采集"

#### Scenario: 表格包含类型表头
- **WHEN** 采集任务表格渲染
- **THEN** 表头行包含"类型"列，位于"主题"列之后
