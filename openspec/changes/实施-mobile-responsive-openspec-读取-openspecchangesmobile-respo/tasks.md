# Tasks

## 1. CSS 响应式规则 [scope: frontend]

- [x] **1.1 替换现有 `@media(max-width:768px)` 规则块**
  在 `<style>` 标签中找到现有 `@media(max-width:768px){.sidebar{width:56px}...}` 规则，替换为完整的移动端响应式规则块，覆盖：body 布局、sidebar 隐藏/浮层、main 全宽、topbar 收窄、content padding 缩减、网格降列（metrics 2列、grid-2 单列、sh-metrics 3列、rcfg 单列、techSignals 2列）、卡片/数字字号缩小、表格横向滚动、feed-item/pager 缩小、drawer 面板全宽、模态框 max-width:95vw

- [x] **1.2 添加汉堡菜单 CSS 和 HTML**
  在 CSS 中添加 `.menu-btn` 默认隐藏、在媒体查询中显示的规则。在 `.topbar` HTML 中 `.title` div 之前添加 `<div class="menu-btn" onclick="toggleMobileMenu()">☰</div>`。添加 `.sidebar.mobile-open` 的 fixed 浮层样式。

## 2. JS 内联样式修复 [scope: frontend]

- [x] **2.1 模态框硬编码宽度替换**
  搜索所有 JS 中 `style="width:520px`、`style="width:500px`、`style="width:640px`、`style="width:400px` 的内联样式，统一替换为 `style="max-width:95vw;width:100%`。涉及函数：`showCollectForm`、`showContentForm`、`showKeywordManager`、`addMonitorRule`、`updateCookie`（两个模式）、`importCookieUI`、`delUser`、`resetPw`、`changeRole`。

- [x] **2.2 JS 内联 grid-template-columns 修复**
  将 `loadSDQuote`、`loadSDTech`、`loadValData` 中 `grid-template-columns:repeat(4,1fr)` 和 `repeat(6,1fr)` 的内联样式替换为使用 CSS class（如 `class="tech-indicators"` 等），确保 CSS 媒体查询规则可以覆盖。

## 3. 汉堡菜单 JS 与 ECharts resize [scope: frontend]

- [x] **3.1 添加 toggleMobileMenu 函数和导航自动关闭**
  在 JS 中添加 `toggleMobileMenu()` 函数，切换 `.sidebar` 的 `mobile-open` class。修改 `initNav` 中的 `a.onclick` 处理函数，在移动端点击导航项后自动移除 `mobile-open` class。

- [x] **3.2 添加 ECharts 移动端 resize 监听**
  在 `init()` 函数末尾添加 `window.matchMedia('(max-width:768px)')` 的 `addListener`/`addEventListener`，在媒体查询变化时遍历所有已注册的 ECharts 实例调用 `resize()`。维护一个全局 `_echartsInstances` 数组，在每次 `echarts.init()` 后将实例 push 进去。
