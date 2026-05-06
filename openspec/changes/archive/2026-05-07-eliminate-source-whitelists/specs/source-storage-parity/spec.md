## ADDED Requirements

### Requirement: 存储层接受所有 DataSource 枚举成员
存储层 SHALL 接受任何通过 DataSource 枚举验证的数据源，不再维护独立的白名单集合。数据源的合法性 SHALL 仅由 DataSource 枚举决定。

#### Scenario: 已注册枚举的源可以存储
- **WHEN** DataItem 的 source 字段为 DataSource 枚举中已注册的成员（如 QTC、C114、ITHOME）
- **THEN** 存储层 SHALL 正常写入数据，不拒绝、不跳过

#### Scenario: 未注册枚举的源被拒绝
- **WHEN** DataItem 的 source 字段不是 DataSource 枚举中的成员
- **THEN** 存储层 SHALL 拒绝该数据项，返回验证错误

#### Scenario: 未来新增枚举成员自动可存储
- **WHEN** 开发者在 DataSource 枚举中新增一个成员并实现对应爬虫
- **THEN** 该源采集的数据 SHALL 无需修改存储层代码即可正常入库

### Requirement: INSERT 时设置 news_type 默认值
`enhanced_financial_news_storage.py` 的 INSERT 语句 SHALL 包含 `news_type` 字段。当数据项未提供 news_type 时，SHALL 使用 `"tech"` 作为默认值。

#### Scenario: 爬虫未设置 news_type
- **WHEN** 爬虫返回的数据项没有 news_type 字段
- **THEN** INSERT 时 SHALL 将 news_type 设为 `"tech"`

#### Scenario: 爬虫已设置 news_type
- **WHEN** 爬虫返回的数据项包含 news_type 字段（如 "policy"、"funding"）
- **THEN** INSERT 时 SHALL 使用爬虫提供的值，不覆盖

### Requirement: API 返回的 count 与实际入库数一致
采集任务 API 返回的 `total_count` SHALL 等于实际成功写入数据库的记录数，而非仅采集到的数量。

#### Scenario: 全部入库成功
- **WHEN** 采集到 17 条数据且全部成功写入数据库
- **THEN** API SHALL 返回 `total_count=17`

#### Scenario: 部分入库失败
- **WHEN** 采集到 20 条数据，其中 3 条因 URL 重复被跳过
- **THEN** API SHALL 返回的 total_count 反映实际新入库数量，不包含被跳过的记录
