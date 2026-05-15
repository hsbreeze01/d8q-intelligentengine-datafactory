# Tasks: 策略组配置表单 UX 改造

## 1. 基础设施（辅助函数与模板定义）

- [ ] 在 `showStrategyForm()` 函数上方添加辅助基础设施：`INDICATOR_OPTIONS` 常量（指标下拉选项列表含 label/value）、`STRATEGY_TEMPLATES` 预设模板对象（底部共振/放量突破/超跌反弹各含 conditions/logic/aggregation）、`OPERATOR_OPTIONS` 运算符选项、以及核心序列化/反序列化函数（`serializeConditions` 将条件行数组→indicators JSON、`parseConditions` 将 indicators JSON→条件行数组、`serializeSignalLogic`/`parseSignalLogic`、`serializeAggregation`/`parseAggregation`）

## 2. 条件构建器 UI（showStrategyForm 主体改造）

- [ ] 改造 `showStrategyForm()` 函数，将「指标配置 JSON textarea」替换为结构化条件构建器区域：顶部预设模板按钮行（复用 `.tpl-opts` 样式）、动态条件行容器（每行包含指标下拉框 + 运算符下拉框 + 数值输入框 + 删除按钮）、底部「+ 添加条件」按钮；实现 `addConditionRow(indicator, operator, value)` 和 `removeConditionRow(btn)` 函数；实现 `applyTemplate(key)` 一键填充模板；编辑模式下调用 `parseConditions()` 回填已有条件

## 3. 信号逻辑与聚合规则控件

- [ ] 将「信号逻辑 JSON textarea」替换为单选按钮组（AND/OR/SCORING）+ SCORING 模式的「最低满足条件数」数字输入框；将「聚合规则 JSON textarea」替换为维度下拉框（industry/concept/theme）+ 最少股票数输入框 + 时间窗口（数值 + 单位下拉框）；编辑模式下分别调用 `parseSignalLogic()` 和 `parseAggregation()` 回填；将扫描频率下拉框从仅 daily 扩展为每小时/每天/每周/自定义 cron 四个选项

## 4. 保存逻辑适配与新增 CSS

- [ ] 改造 `saveStrategyGroup()` 函数，从新的结构化控件读取值：调用 `serializeConditions()` 组装 indicators、`serializeSignalLogic()` 组装 signal_logic、`serializeAggregation()` 组装 aggregation、频率下拉框获取 scan_frequency；在 `<style>` 中追加 `.cond-row` 等 CSS 样式（flex 布局，gap 间距，与现有 UI 风格一致）；确保所有交互（新建/编辑/模板填充/保存）端到端可用
