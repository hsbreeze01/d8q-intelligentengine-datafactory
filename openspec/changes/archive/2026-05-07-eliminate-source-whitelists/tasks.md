## 1. 删除存储层冗余白名单

- [x] 1.1 在 `financial_news_storage_tools.py` 中删除 `financial_sources` 硬编码集合，将白名单检查改为基于 `DataSource(source_value)` 枚举验证（try/except ValueError）
- [x] 1.2 在 `financial_news_storage.py` 中删除 `financial_platforms` 硬编码集合，改为从 DataSource 枚举推导：所有枚举成员均可存储

## 2. INSERT 增加 news_type 默认值

- [x] 2.1 在 `enhanced_financial_news_storage.py` 的 INSERT SQL 中增加 `news_type` 列，从 DataItem metadata 中读取或默认为 `"tech"`

## 3. 验证测试

- [x] 3.1 运行现有数据源（财联社/NBD/36kr）采集任务，验证入库不受影响
- [x] 3.2 运行量子计算采集任务，验证 qtc/c114/ithome 数据正常入库且 news_type 不为空
- [x] 3.3 查询 DB 确认新入库数据有 news_type 值，Feed 页类型过滤可匹配
