## ADDED Requirements

### Requirement: Track selector in collection task modal
采集任务创建弹窗 SHALL 在主题输入框上方新增"采集模式"切换控件，提供"按赛道"和"自定义"两个选项。选择"按赛道"时显示赛道下拉列表。

#### Scenario: Switch to track mode
- **WHEN** 用户点击"按赛道"模式
- **THEN** 显示赛道下拉框（从 `/api/proxy/tracks` 加载所有 active 赛道）
- **AND** 主题输入框变为只读，数据源复选框变为只读
- **AND** 下方显示所选赛道的关键词标签列表

#### Scenario: Switch back to custom mode
- **WHEN** 用户切换回"自定义"模式
- **THEN** 隐藏赛道下拉框和关键词列表
- **AND** 主题输入框和数据源复选框恢复可编辑

### Requirement: Auto-fill from track selection
选择赛道后 SHALL 自动填充主题和数据源。

#### Scenario: Select track auto-fills form
- **WHEN** 用户在下拉框中选择"新材料"赛道
- **THEN** 主题输入框自动设为"新材料"（只读）
- **AND** 数据源自动设置为该赛道的默认源（只读，可展示但不允许修改）

### Requirement: Show track keywords
选择赛道后 SHALL 展示该赛道的关键词列表。

#### Scenario: Display keywords as chips
- **WHEN** 用户选择"新材料"赛道
- **THEN** 从 `/api/proxy/tracks/{id}/keywords` 获取关键词列表
- **AND** 以标签 chips 形式展示在赛道选择器下方
- **AND** 关键词区域限高 120px，超出部分可滚动

### Requirement: Submit track_id when saving
保存赛道模式的任务时 SHALL 发送 track_id 到后端。

#### Scenario: Save with track_id
- **WHEN** 赛道模式下用户点击"保存"
- **THEN** POST body 包含 `track_id` 字段（赛道的 id 值）
- **AND** 不包含 `sources` 字段（由后端自动填充）

#### Scenario: Save custom mode without track_id
- **WHEN** 自定义模式下用户点击"保存"
- **THEN** POST body 不包含 `track_id`，行为与改动前完全一致

### Requirement: Track badge in task list
任务列表中，赛道任务 SHALL 显示赛道颜色标签。

#### Scenario: Track task shows colored badge
- **WHEN** 任务有 track_id=3（新材料，颜色 #faad14）
- **THEN** 任务主题旁显示"新材料"彩色标签

#### Scenario: Custom task shows no badge
- **WHEN** 任务无 track_id
- **THEN** 不显示赛道标签，与改动前一致

### Requirement: Factory proxy for keywords API
Factory SHALL 新增 `/api/proxy/tracks/<id>/keywords` 代理路由，转发到 data-agent 的 `GET /api/tracks/{id}/keywords`。

#### Scenario: Proxy keywords request
- **WHEN** 前端请求 `/api/proxy/tracks/3/keywords`
- **THEN** Factory 转发到 `http://localhost:8000/api/tracks/3/keywords`
- **AND** 返回 `{"track_id": 3, "keywords": [...], "count": 30}`
