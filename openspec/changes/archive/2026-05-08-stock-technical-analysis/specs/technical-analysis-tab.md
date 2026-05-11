# Delta Spec: 个股详情页技术分析 Tab

## MODIFIED Requirements

### Requirement: switchSDTab('tech') 技术分析面板渲染

When the user selects the "技术分析" tab on a stock detail page, the system SHALL render a full technical analysis panel replacing the current placeholder content.

#### Scenario: 用户点击技术分析 Tab 展示面板

- **Given** 用户已打开个股详情页 `/stock/{code}`
- **When** 用户点击 "技术分析" Tab（调用 `switchSDTab('tech')`）
- **Then** 系统 SHALL 在该 Tab 区域渲染一个技术分析面板，包含以下子区域：
  1. 指标图表区域（支持 MA / MACD / KDJ / BOLL / RSI 切换）
  2. 技术信号汇总面板
  3. 综合判定文字

---

### Requirement: 技术指标图表切换

The system SHALL provide an indicator selector that allows the user to switch between MA, MACD, KDJ, BOLL, and RSI chart visualizations using ECharts.

#### Scenario: 用户切换技术指标图表

- **Given** 技术分析面板已渲染
- **And** 系统已获取该股票的 K 线数据（复用 `loadSDQuote` 中已有的行情数据）
- **When** 用户选择某个技术指标（如 MACD）
- **Then** 系统 SHALL 使用 ECharts 绘制对应的指标图表
- **And** MA 指标 SHALL 在 K 线图上叠加绘制 MA5 / MA10 / MA20 / MA60 均线
- **And** MACD 指标 SHALL 绘制 DIF、DEA 双线及 MACD 柱状图
- **And** KDJ 指标 SHALL 绘制 K、D、J 三线
- **And** BOLL 指标 SHALL 在 K 线图上叠加绘制上轨、中轨、下轨
- **And** RSI 指标 SHALL 绘制 RSI6、RSI12、RSI24 三线
- **And** 默认选中 SHALL 为 MA

#### Scenario: 图表数据来源

- **Given** 技术分析面板需要 K 线历史数据来计算指标
- **When** 面板渲染时
- **Then** 系统 SHALL 复用页面已有的 `loadSDQuote` 函数中获取的行情数据
- **And** 若行情数据尚不可用，系统 SHALL 调用 `/api/stock/quote` 获取数据后再绘制
- **And** 指标计算 SHALL 在浏览器端使用 JavaScript 完成，不依赖后端新增 API

---

### Requirement: 技术信号汇总面板

The system SHALL display a signal summary panel listing each technical indicator's current value and buy/sell signal judgment.

#### Scenario: 展示技术信号汇总

- **Given** 技术分析面板已渲染
- **And** K 线历史数据已加载
- **When** 面板完成指标计算
- **Then** 系统 SHALL 展示一个信号汇总面板，每一行包含：
  - 指标名称（如 MA、MACD、KDJ、BOLL、RSI）
  - 当前关键数值
  - 信号判定文字（看多 / 看空 / 中性）
- **And** 信号判定 SHALL 基于最后一根 K 线的指标值计算
- **And** 看多信号 SHALL 使用绿色标识
- **And** 看空信号 SHALL 使用红色标识
- **And** 中性信号 SHALL 使用灰色标识

#### Scenario: 信号判定规则

- **Given** 需要对各指标给出信号判定
- **When** 计算最后一根 K 线的指标值
- **Then** 系统 SHALL 按以下规则判定：
  - **MA**: 短期均线（MA5）上穿长期均线（MA20）为看多，下穿为看空，否则中性
  - **MACD**: DIF 上穿 DEA（金叉）为看多，DIF 下穿 DEA（死叉）为看空，否则中性；MACD 柱由负转正为辅助看多
  - **KDJ**: K > D 且 J < 80 为看多；K < D 且 J > 20 为看空；否则中性
  - **BOLL**: 价格触及下轨反弹为看多；触及上轨回落为看空；否则中性
  - **RSI**: RSI < 30 为看多（超卖）；RSI > 70 为看空（超买）；否则中性

---

### Requirement: 综合判定文字

The system SHALL display an overall technical assessment based on the aggregation of all individual indicator signals.

#### Scenario: 展示综合技术判定

- **Given** 各技术指标的信号判定已计算完成
- **When** 信号汇总面板渲染完成
- **Then** 系统 SHALL 在信号面板下方展示综合判定文字
- **And** 综合判定 SHALL 统计所有指标中看多、看空、中性的数量
- **And** 若看多信号 ≥ 3 个，综合判定文字 SHALL 为"技术面偏多"
- **And** 若看空信号 ≥ 3 个，综合判定文字 SHALL 为"技术面偏空"
- **And** 其他情况综合判定文字 SHALL 为"技术面中性"
- **And** 综合判定文字 SHALL 附加免责提示："以上技术分析仅供参考，不构成投资建议"

---

## ADDED Requirements

### Requirement: 前端技术指标计算函数库

The system SHALL include a set of pure JavaScript functions for computing MA, MACD, KDJ, BOLL, and RSI from an array of OHLCV data points.

#### Scenario: 计算各类技术指标

- **Given** 系统需要在前端计算技术指标
- **When** 有可用的 OHLCV（Open/High/Low/Close/Volume）历史数据数组
- **Then** 系统 SHALL 提供 `calcMA(closes, periods)` 函数返回各周期均线值数组
- **And** SHALL 提供 `calcMACD(closes, short=12, long=26, signal=9)` 函数返回 DIF、DEA、MACD 柱值数组
- **And** SHALL 提供 `calcKDJ(highs, lows, closes, n=9, m1=3, m2=3)` 函数返回 K、D、J 值数组
- **And** SHALL 提供 `calcBOLL(closes, n=20, k=2)` 函数返回上轨、中轨、下轨值数组
- **And** SHALL 提供 `calcRSI(closes, periods=[6,12,24])` 函数返回各周期 RSI 值数组
- **And** 所有计算函数 SHALL 为纯函数，无副作用，仅依赖传入数据
