# Design: 策略组配置表单 UX 改造

## 架构决策

### 纯前端改造
- **范围**：仅修改 `templates/index.html` 中的 `showStrategyForm()` 和 `saveStrategyGroup()` 函数
- **后端不动**：API 接口（`POST/PUT /api/strategy/groups`）和 Pydantic 模型保持不变
- **数据兼容**：提交时由前端 JS 组装与原 JSON textarea 相同格式的请求体

### 指标列表来源
- 硬编码一份 `indicators_daily` 列映射表（从 compass 服务 `indicators_daily` 表结构提取常用列）
- 不调用后端 API 获取列名，避免增加新接口
- 初始映射：`kdj_k`, `kdj_d`, `kdj_j`, `rsi_6`, `rsi_12`, `rsi_24`, `volume_ratio`, `turnover_rate`, `macd`, `dif`, `dea`, `ma_5`, `ma_10`, `ma_20`, `boll_upper`, `boll_mid`, `boll_lower`, `close`, `open`, `high`, `low`, `pe_ttm`, `pb`, `ps`

### 预设模板
- 硬编码 3 个常用策略模板，通过按钮一键填充条件构建器
- 模板定义为 JS 对象，包含指标条件和信号逻辑

## 数据流

```
用户操作条件构建器 / 单选 / 下拉框
       ↓
JavaScript 组装请求体:
{
  name: string,
  description: string,
  scan_frequency: string,        // daily | hourly | weekly | cron表达式
  indicators: {                  // 从条件行数组构建
    kdj: {conditions: ["k<30"]},
    rsi: {conditions: ["rsi_6<30"]},
    volume: {conditions: ["volume_ratio>1.5"]}
  },
  signal_logic: {                // 从单选按钮构建
    type: "SCORING" | "AND" | "OR",
    min_signals?: number
  },
  aggregation: {                 // 从结构化字段构建
    dimension: "industry" | "concept" | "theme",
    min_stocks: number,
    time_window_days?: number,
    time_window_hours?: number
  }
}
       ↓
POST/PUT /api/strategy/groups （与旧版完全相同的 payload）
```

## 指标条件解析/序列化

### 序列化（表单 → JSON）
- 条件行数组 `[{indicator, operator, value}]` → 按 indicator 分组 → `{kdj: {conditions: ["k<30"]}}` 格式
- `cross_above`/`cross_below` 运算符映射为 `indicator cross_above value` 字符串
- 简单比较运算符映射为 `indicator<value` 格式

### 反序列化（JSON → 表单回填）
- 解析 `{kdj: {conditions: ["k<30"]}}` → 提取 `[{indicator: "kdj_k", operator: "<", value: 30}]`
- 支持解析格式：`indicator运算符value`，如 `k<30`、`rsi_6<30`、`volume_ratio>1.5`
- `cross_above`/`cross_below` 检测为含空格的三段式

## 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `templates/index.html` — `showStrategyForm()` | 将 3 个 JSON textarea + 频率 select 替换为结构化控件 |
| `templates/index.html` — `saveStrategyGroup()` | 从新控件读取值并组装 JSON |
| `templates/index.html` — 新增辅助函数 | `parseConditions()`, `serializeConditions()`, `parseSignalLogic()`, `serializeSignalLogic()`, `parseAggregation()`, `serializeAggregation()`, `applyTemplate()`, `addConditionRow()`, `removeConditionRow()` |

## 关键设计细节

### 条件构建器 HTML 结构
```
<div id="condBuilder">
  <div class="tpl-opts">
    <div class="tpl-opt" onclick="applyTemplate('bottom_resonance')">底部共振</div>
    <div class="tpl-opt" onclick="applyTemplate('volume_breakout')">放量突破</div>
    <div class="tpl-opt" onclick="applyTemplate('oversold_bounce')">超跌反弹</div>
  </div>
  <div id="condRows">
    <!-- 动态条件行 -->
    <div class="cond-row">
      <select class="cond-indicator">...</select>
      <select class="cond-operator">...</select>
      <input type="number" class="cond-value">
      <button onclick="removeConditionRow(this)">×</button>
    </div>
  </div>
  <button onclick="addConditionRow()">+ 添加条件</button>
</div>
```

### CSS 复用
- 使用已有的 `.tpl-opts`, `.tpl-opt`, `.search` (作为 input/select 基础样式), `.btn`, `.btn-ghost` 等样式类
- 条件行新增 `.cond-row` 样式，使用 flex 布局，与现有 UI 风格一致
- 无需新增独立 CSS 文件，在 `<style>` 中追加即可

### 预设模板定义
```javascript
var STRATEGY_TEMPLATES = {
  bottom_resonance: {
    name: '底部共振策略',
    conditions: [
      {indicator: 'kdj_k', operator: '<', value: 30},
      {indicator: 'rsi_6', operator: '<', value: 30},
      {indicator: 'volume_ratio', operator: '>', value: 1.5}
    ],
    logic: {type: 'SCORING', min_signals: 2},
    aggregation: {dimension: 'industry', min_stocks: 3, time_window_days: 3}
  },
  volume_breakout: {
    name: '放量突破策略',
    conditions: [
      {indicator: 'volume_ratio', operator: '>', value: 2.0},
      {indicator: 'close', operator: 'cross_above', value: 0}, // cross_above ma_20
      {indicator: 'macd', operator: '>', value: 0}
    ],
    logic: {type: 'AND'},
    aggregation: {dimension: 'concept', min_stocks: 3, time_window_days: 5}
  },
  oversold_bounce: {
    name: '超跌反弹策略',
    conditions: [
      {indicator: 'kdj_j', operator: '<', value: 0},
      {indicator: 'rsi_6', operator: '<', value: 20},
      {indicator: 'close', operator: '<', value: 0} // below boll_lower — simplified
    ],
    logic: {type: 'OR'},
    aggregation: {dimension: 'industry', min_stocks: 5, time_window_days: 7}
  }
};
```

## 前端任务标注

> ⚠️ 本 change 为纯前端改造，所有任务均为 `scope: frontend`，涉及 `templates/index.html` 中的 JavaScript 和 HTML 模板字符串修改。zsiga 将执行这些任务。
