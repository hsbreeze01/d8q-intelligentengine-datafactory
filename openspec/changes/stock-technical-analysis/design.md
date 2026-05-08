# Design: 个股详情页技术分析 Tab

## 架构决策

### 决策 1: 纯前端实现，无新增后端 API

**理由**: 技术指标（MA/MACD/KDJ/BOLL/RSI）的计算为纯数学运算，数据量有限（通常 60~250 根 K 线），浏览器端完全可以实时计算。复用页面已有的 `/api/stock/quote` 接口获取行情数据，无需新增或修改后端代码。

### 决策 2: 内联 JavaScript 到 index.html

**理由**: 项目现有模式为单文件 SPA（`templates/index.html`），所有前端逻辑内联于该文件。遵循此模式，将技术指标计算函数和 ECharts 绑定逻辑直接写入 `index.html` 的 `<script>` 块中。

### 决策 3: 复用 ECharts CDN

**理由**: 项目 `index.html` 已通过 CDN 引入 ECharts。直接使用现有的 ECharts 实例进行图表渲染，无需引入额外依赖。

## 数据流

```
用户点击 "技术分析" Tab
    │
    ▼
switchSDTab('tech')
    │
    ├── 检查页面是否已有 K 线数据（window._sdKlineData 或类似变量）
    │   ├── 有 → 直接使用
    │   └── 无 → 调用 /api/stock/quote 获取
    │
    ├── 调用 calcXxx() 函数计算各指标
    │
    ├── 渲染 UI 结构（指标选择器 + 图表区 + 信号面板 + 综合判定）
    │
    ├── 默认绘制 MA 指标图表
    │
    └── 计算并渲染信号汇总面板 + 综合判定文字
```

## 需要修改的文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `templates/index.html` | MODIFY | (1) 在 `switchSDTab('tech')` 分支中替换占位符，渲染完整技术分析面板；(2) 新增技术指标计算函数 `calcMA`/`calcMACD`/`calcKDJ`/`calcBOLL`/`calcRSI`；(3) 新增 ECharts 指标图表绘制函数 `drawTechMA`/`drawTechMACD`/`drawTechKDJ`/`drawTechBOLL`/`drawTechRSI`；(4) 新增信号判定函数 `evalSignals` 和综合判定函数 `renderVerdict` |

**不需要新增文件，不需要修改后端。**

## 技术细节

### 数据来源
- 复用 `loadSDQuote` 函数中获取的行情数据（`window._sdQuoteData`）
- 若无可用的 K 线数据，调用 `/api/stock/quote?symbol={code}` 获取日线数据
- 行情数据格式为 OHLCV 数组：`[{date, open, high, low, close, volume}, ...]`

### ECharts 图表配置
- MA: K 线 + 均线叠加（candlestick + 4 条 line series）
- MACD: 柱状图 + 双线（bar + 2 条 line series），使用 ECharts grid 分区
- KDJ: 三线图（3 条 line series）
- BOLL: K 线 + 三条轨道线（candlestick + 3 条 line series）
- RSI: 三线图（3 条 line series），带 30/70 参考线（markLine）

### 信号汇总面板样式
- 采用卡片式布局，每个指标一行
- 使用 Bootstrap 行内样式（项目已有 Bootstrap CDN）
- 看多用 `text-success`，看空用 `text-danger`，中性用 `text-muted`

### 综合判定
- 以醒目的面板样式展示
- 包含免责声明文字
