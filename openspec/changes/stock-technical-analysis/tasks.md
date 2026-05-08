# Tasks: 个股详情页技术分析 Tab

## 1. 技术指标计算函数

- [x] **1.1** 在 `templates/index.html` 的 `<script>` 块中新增纯函数 `calcMA(closes, periods)`、`calcEMA(closes, period)`（EMA 为 MACD 的基础）
- [ ] **1.2** 在 `templates/index.html` 中新增 `calcMACD(closes, short, long, signal)` 函数，返回 `{dif[], dea[], macd[]}`
- [ ] **1.3** 在 `templates/index.html` 中新增 `calcKDJ(highs, lows, closes, n, m1, m2)` 函数，返回 `{k[], d[], j[]}`
- [ ] **1.4** 在 `templates/index.html` 中新增 `calcBOLL(closes, n, k)` 函数，返回 `{upper[], mid[], lower[]}`
- [ ] **1.5** 在 `templates/index.html` 中新增 `calcRSI(closes, periods)` 函数，返回各周期 RSI 值数组

## 2. ECharts 指标图表绘制函数

- [ ] **2.1** 新增 `drawTechMA(containerId, klineData)` 函数：K 线 + MA5/MA10/MA20/MA60 均线叠加
- [ ] **2.2** 新增 `drawTechMACD(containerId, klineData)` 函数：DIF/DEA 双线 + MACD 柱状图，使用双 grid 布局
- [ ] **2.3** 新增 `drawTechKDJ(containerId, klineData)` 函数：K/D/J 三线图
- [ ] **2.4** 新增 `drawTechBOLL(containerId, klineData)` 函数：K 线 + 上轨/中轨/下轨
- [ ] **2.5** 新增 `drawTechRSI(containerId, klineData)` 函数：RSI6/RSI12/RSI24 + 30/70 参考线

## 3. 信号判定与综合判定

- [ ] **3.1** 新增 `evalSignals(klineData)` 函数，计算每个指标（MA/MACD/KDJ/BOLL/RSI）的信号判定（看多/看空/中性），返回 `[{name, values, signal}]`
- [ ] **3.2** 新增 `renderSignalPanel(container, signals)` 函数，渲染信号汇总卡片列表（指标名 + 数值 + 信号标签）
- [ ] **3.3** 新增 `renderVerdict(container, signals)` 函数，统计多空信号数量，渲染综合判定文字 + 免责提示

## 4. switchSDTab('tech') 面板整合

- [ ] **4.1** 修改 `switchSDTab` 函数的 `case 'tech'` 分支：替换占位符为完整 HTML 结构（指标选择器按钮栏 + 图表容器 div + 信号面板容器 + 综合判定容器）
- [ ] **4.2** 在 tech case 中添加数据获取逻辑：复用已有行情数据或调用 `/api/stock/quote`，然后计算指标、绘制默认 MA 图表、渲染信号面板和综合判定
- [ ] **4.3** 为指标选择器按钮绑定点击事件：点击时调用对应的 `drawTechXxx` 函数切换图表

## 5. 样式与验证

- [ ] **5.1** 添加技术分析面板的行内 CSS 样式（指标选择器按钮栏、图表容器高度、信号面板卡片样式），确保与现有页面风格一致
