# Spec: 策略组配置表单结构化控件

## MODIFIED Requirements

### Requirement: 指标条件输入方式

策略管理页面的指标配置区域 SHALL 将 JSON 文本框替换为**条件构建器**，允许用户通过 UI 控件动态添加、删除条件行。

#### Scenario: 用户通过条件构建器添加指标条件

- Given 用户打开新建或编辑策略组表单
- When 指标配置区域渲染完成
- Then 系统 SHALL 显示一个条件构建器区域，每行包含三个控件：
  - 指标下拉框：从 `indicators_daily` 表列自动生成选项列表
  - 运算符下拉框：包含 `>`, `<`, `>=`, `<=`, `==`, `cross_above`, `cross_below`
  - 数值输入框：接受浮点数
- And 每行右侧 SHALL 有一个「删除」按钮，点击后移除该条件行
- And 区域底部 SHALL 有一个「+ 添加条件」按钮

#### Scenario: 表单从指标条件构建器组装 JSON 提交

- Given 用户通过条件构建器配置了 3 条条件：`kdj_k < 30`、`rsi_6 < 30`、`volume_ratio > 1.5`
- When 用户点击「保存」
- Then 系统 SHALL 将条件构建器中的所有条件行组装为与原 JSON textarea 相同格式的 `indicators` 字段
- And 提交的请求体 SHALL 与手动输入等价 JSON 的请求体完全一致

#### Scenario: 编辑已有策略组时回填条件构建器

- Given 用户点击编辑一个已有策略组，该策略组的 `indicators` 字段为 `{kdj:{conditions:["k<30"]}, rsi:{conditions:["rsi_6<30"]}}`
- When 表单渲染完成
- Then 条件构建器 SHALL 解析已有 JSON 并自动回填对应条件行
- And 每条已有条件 SHALL 正确映射到指标下拉框、运算符下拉框和数值输入框

#### Scenario: 预设策略模板快速填充

- Given 用户打开新建策略组表单
- When 指标配置区域渲染完成
- Then 区域顶部 SHALL 显示预设模板按钮（如「底部共振」「放量突破」「超跌反弹」）
- And 点击任一模板 SHALL 自动填充条件构建器的条件行
- And 用户 SHALL 能在模板填充后继续增删条件行

---

### Requirement: 信号逻辑输入方式

策略管理页面的信号逻辑区域 SHALL 将 JSON 文本框替换为**单选按钮组 + 条件输入**。

#### Scenario: 用户选择信号逻辑类型

- Given 用户打开新建或编辑策略组表单
- When 信号逻辑区域渲染完成
- Then 系统 SHALL 显示三个单选项：
  - **AND（全部满足）**
  - **OR（任一满足）**
  - **SCORING（评分模式）**
- And 选中 SCORING 时 SHALL 额外显示「最低满足条件数」数字输入框

#### Scenario: 信号逻辑组装 JSON 提交

- Given 用户选择了「SCORING」模式并输入最低满足条件数为 2
- When 用户点击「保存」
- Then 系统 SHALL 组装为 `{type:"SCORING", min_signals:2}` 格式的 `signal_logic` 字段
- And 选择 AND 时组装为 `{type:"AND"}`
- And 选择 OR 时组装为 `{type:"OR"}`

#### Scenario: 编辑已有策略组时回填信号逻辑

- Given 用户编辑一个已有策略组，`signal_logic` 为 `{type:"SCORING", min_signals:2}`
- When 信号逻辑区域渲染完成
- Then 系统 SHALL 自动选中「SCORING」单选按钮
- And 「最低满足条件数」输入框 SHALL 显示 2

---

### Requirement: 聚合规则输入方式

策略管理页面的聚合规则区域 SHALL 将 JSON 文本框替换为**结构化表单控件**。

#### Scenario: 用户配置聚合规则

- Given 用户打开新建或编辑策略组表单
- When 聚合规则区域渲染完成
- Then 系统 SHALL 显示：
  - 维度下拉框：选项为 `industry`（行业）、`concept`（概念）、`theme`（主题）
  - 最少股票数：数字输入框，默认值为 3
  - 时间窗口：数字输入框 + 单位选择下拉框（分钟/小时/天），默认为 3 天

#### Scenario: 聚合规则组装 JSON 提交

- Given 用户选择维度为 `industry`，最少股票数为 3，时间窗口为 3 天
- When 用户点击「保存」
- Then 系统 SHALL 组装为 `{dimension:"industry", min_stocks:3, time_window_days:3}` 格式的 `aggregation` 字段
- And 时间窗口为小时时，SHALL 使用 `time_window_hours` 键
- And 时间窗口为分钟时，SHALL 使用 `time_window_minutes` 键

#### Scenario: 编辑已有策略组时回填聚合规则

- Given 用户编辑一个已有策略组，`aggregation` 为 `{dimension:"industry", min_stocks:3, time_window_days:3}`
- When 聚合规则区域渲染完成
- Then 维度下拉框 SHALL 选中 `industry`
- And 最少股票数 SHALL 显示 3
- And 时间窗口数值 SHALL 显示 3，单位 SHALL 选中「天」

---

### Requirement: 扫描频率扩展

策略管理页面的扫描频率 SHALL 从固定 `daily` 扩展为多选项下拉框。

#### Scenario: 用户选择扫描频率

- Given 用户打开新建或编辑策略组表单
- When 扫描频率下拉框渲染完成
- Then 选项 SHALL 包含：每小时、每天、每周、自定义 cron
- And 选择「自定义 cron」时 SHALL 显示 cron 表达式文本输入框

#### Scenario: 扫描频率提交格式

- Given 用户选择了「每天」
- When 用户点击「保存」
- Then `scan_frequency` 字段 SHALL 为 `daily`
- And 选择「每小时」时 SHALL 为 `hourly`
- And 选择「每周」时 SHALL 为 `weekly`
- And 选择「自定义 cron」时 SHALL 为用户输入的 cron 表达式字符串

---

## ADDED Requirements

### Requirement: 表单数据向后兼容

表单提交时组装的 JSON 结构 SHALL 与原有 JSON textarea 手动输入时的结构完全一致，确保后端 API 无需任何修改。

#### Scenario: 新表单提交的数据被后端正常接受

- Given 用户通过新的结构化表单完成所有配置并提交
- When 请求发送到 `POST /api/strategy/groups` 或 `PUT /api/strategy/groups/:id`
- Then 后端 SHALL 正常处理，不产生解析错误
- And 存储的数据结构 SHALL 与旧版表单提交的结果一致
