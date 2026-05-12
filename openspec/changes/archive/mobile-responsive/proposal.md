# Proposal: 移动端响应式适配

## 背景
当前 factory 前端（`templates/index.html`）为纯 PC 端设计，在手机浏览器（390×844 视口）上有严重布局问题。已有 1 条 `@media(max-width:768px)` 规则但仅缩小侧边栏至 56px，远远不够。

## 目标
使 `templates/index.html` 在 390px-768px 移动端视口下可用且美观，不改变 PC 端现有行为。

## 已验证的问题（Playwright iPhone 14 模拟）

1. **侧边栏占 56px**：移动端应完全隐藏，改为顶部汉堡菜单按钮
2. **概览页指标 4 列挤压**：`.metrics { repeat(4,1fr) }` 导致卡片极窄，第 4 个溢出不可见 → 改为 2 列
3. **ECharts 图表溢出**：`.grid-2` 双栏布局图表只有 108px 宽 → 改为单列堆叠
4. **分页器溢出**：10 个页码按钮超出 390px 视口 → 需要简化或收缩
5. **详情面板不可见**：右侧详情面板从 x=390 开始，完全在视口外 → 需要全屏覆盖
6. **股票详情 6 列指标**：`.sh-metrics { repeat(6,1fr) }` → 改为 3 列
7. **技术指标 4 列**：多处 inline `repeat(4,1fr)` → 改为 2 列
8. **模态框宽度**：部分 JS 内联 `width:700px` → 已有 `max-width:95vw` 但需确认全部

## 方案
纯 CSS 响应式补丁：在现有 `<style>` 末尾追加一套 `@media(max-width:768px)` 规则。对 JS 内联样式中的硬编码宽度做最小改动。

## 范围
- 仅修改 `templates/index.html`
- 不引入新依赖
- 不改变任何功能逻辑
- PC 端（>768px）行为不变

## 文件
- `templates/index.html`（唯一修改文件）
