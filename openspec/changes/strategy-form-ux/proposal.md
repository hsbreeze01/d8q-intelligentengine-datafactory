# Proposal: 策略组配置表单 UX 改造

## Summary
将策略管理页面的 JSON 文本框替换为结构化表单控件，让非技术用户也能配置策略组。

## Motivation
当前 `showStrategyForm()` 中的指标配置、信号逻辑、聚合规则三个字段均为 JSON textarea，用户需要手写 JSON。这导致：
1. 非技术用户无法使用
2. JSON 语法错误频发（括号不匹配、缺少引号）
3. 用户不知道有哪些可用指标和运算符

## Expected Behavior

### 指标条件（原 indicators + signal_logic）
- **条件构建器**：动态添加/删除条件行
- 每行包含：指标下拉框（从 indicators_daily 列自动生成）、运算符下拉框（>, <, >=, <=, ==, cross_above, cross_below）、数值输入框
- 预设常用模板（底部共振、放量突破、超跌反弹）

### 信号逻辑（原 signal_logic JSON）
- **单选按钮组**：AND（全部满足）/ OR（任一满足）/ SCORING（评分模式）
- SCORING 模式时显示"最低满足条件数"数字输入框

### 聚合规则（原 aggregation JSON）
- **结构化表单**：
  - 维度：下拉框（行业 industry / 概念 concept / 主题 theme）
  - 最少股票数：数字输入框（默认 3）
  - 时间窗口：数字输入框 + 单位选择（分钟/小时/天）

### 扫描频率
- 从固定 `daily` 扩展为下拉框：每小时 / 每天 / 每周 / 自定义 cron

## Scope
- **仅前端**：修改 `templates/index.html` 中的 `showStrategyForm()` 函数
- **后端不动**：API 接口和 Pydantic 模型保持不变
- **数据兼容**：表单提交时组装与当前 JSON textarea 相同的请求体

## Out of Scope
- 后端 API 改动
- 数据库 schema 变更
- 策略发现/我的策略页面

## Target Project
d8q-intelligentengine-datafactory (前端), d8q-intelligentengine-stockcompass (API reference)
