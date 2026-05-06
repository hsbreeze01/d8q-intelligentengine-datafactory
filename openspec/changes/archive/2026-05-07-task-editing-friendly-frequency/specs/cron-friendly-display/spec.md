## ADDED Requirements

### Requirement: cron 表达式友好展示
任务列表的频率列 SHALL 将 cron 表达式转换为中文描述展示，而非显示原始 cron 字符串。系统 SHALL 维护一个 cron 到中文的映射表，对未匹配的 cron 表达式 fallback 显示原始值。

#### Scenario: 已知 cron 模式展示
- **WHEN** 任务的 cron_expr 为 `0 */2 * * *`
- **THEN** 频率列 SHALL 显示"每2小时"

#### Scenario: 另一个已知 cron 模式
- **WHEN** 任务的 cron_expr 为 `0 9 * * 1-5`
- **THEN** 频率列 SHALL 显示"工作日每天1次"

#### Scenario: 未知 cron 模式 fallback
- **WHEN** 任务的 cron_expr 不在映射表中
- **THEN** 频率列 SHALL 显示原始 cron 表达式值

#### Scenario: 空频率
- **WHEN** 任务的 cron_expr 为空或 null
- **THEN** 频率列 SHALL 显示"-"

### Requirement: cron 映射表覆盖范围
系统 SHALL 至少覆盖以下 cron 到中文的映射：

| cron_expr | 中文标签 |
|-----------|----------|
| `0 */1 * * *` | 每小时 |
| `0 */2 * * *` | 每2小时 |
| `0 */4 * * *` | 每4小时 |
| `0 */6 * * *` | 每6小时 |
| `0 8,12,18 * * *` | 每天3次(8/12/18点) |
| `0 9 * * *` | 每天1次(9点) |
| `0 9 * * 1-5` | 工作日每天1次 |

#### Scenario: 映射表完整性
- **WHEN** 系统初始化
- **THEN** 映射表 SHALL 包含上述所有 7 种 cron 模式对应的中文标签

### Requirement: 创作/发布任务频率友好展示
创作/发布任务列表的频率列 SHALL 直接展示 `freq` 字段的中文描述（daily→每日、weekly→每周、monthly→每月），不涉及 cron 转换。

#### Scenario: daily 频率展示
- **WHEN** 创作/发布任务的 freq 为 "daily"
- **THEN** 频率列 SHALL 显示"每日"

#### Scenario: weekly 频率展示
- **WHEN** 创作/发布任务的 freq 为 "weekly"
- **THEN** 频率列 SHALL 显示"每周"

#### Scenario: monthly 频率展示
- **WHEN** 创作/发布任务的 freq 为 "monthly"
- **THEN** 频率列 SHALL 显示"每月"
