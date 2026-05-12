# Tasks

## Task 1: CSS 响应式规则 [必做]
在 `<style>` 标签末尾（`/* === 资讯 Feed 样式 === */` 之前）追加 `@media(max-width:768px)` 规则块，覆盖以下选择器：

### 1.1 整体布局
- `body` → `flex-direction: column`（sidebar 变成顶部或隐藏）
- `.sidebar` → `display: none`（完全隐藏，后续加汉堡菜单）
- `.main` → `width: 100%; overflow-x: hidden`
- `.topbar` → `padding: 0 12px`
- `.topbar .search` → `width: 120px; font-size: 12px`
- `.content` → `padding: 12px`

### 1.2 网格降列
- `.metrics` → `grid-template-columns: repeat(2, 1fr)`
- `.grid-2` → `grid-template-columns: 1fr`（单列堆叠）
- `.sh-metrics` → `grid-template-columns: repeat(3, 1fr)`
- `.rcfg` → `grid-template-columns: 1fr`

### 1.3 卡片与内容
- `.mc .value` → `font-size: 22px`（缩小数字）
- `.card` → `padding: 14px`
- `.card h3` → `font-size: 14px`
- `.et` → 外层包裹 `overflow-x: auto`（用 `display:block; overflow-x:auto`）

### 1.4 Feed 与分页
- `.feed-item` → `padding: 12px 14px`
- `.feed-pager` → `.fp { min-width: 28px; height: 28px; font-size: 11px }`

### 1.5 详情面板
- 右侧详情面板（class 含 `detail` 或 id 含 `detail`）→ `position: fixed; inset: 0; width: 100%; z-index: 100`

### 1.6 模态框
- `#taskModal` 内的 `.card` → `width: 100% !important; max-width: 95vw !important`

## Task 2: JS 内联样式修复 [必做]
在 `@media` 之后的 JS 中搜索以下硬编码宽度，改为响应式：

### 2.1 模态框宽度
搜索所有 `width:520px`、`width:560px`、`width:640px`、`width:680px`、`width:700px` 的内联样式。
对每个找到的位置，将固定宽度替换为 `max-width:95vw;width:100%` 的写法。

重点搜索这些函数中的内联 HTML：
- `importCookieUI()` — 已改为 `width:640px`，确认 `max-width:95vw` 存在
- `updateCookie()` — 含 `width:520px` 的模态框
- 其他 `modal.innerHTML` 赋值

### 2.2 股票详情指标
搜索 JS 中所有 `grid-template-columns:repeat(4,1fr)` 和 `repeat(6,1fr)` 的内联样式。
改为使用 CSS class 而非内联样式，确保响应式规则可覆盖。

### 2.3 技术指标区域
搜索 `techIndicators`、`techSignals` 相关的内联 grid 样式，同上处理。

## Task 3: 侧边栏汉堡菜单 [建议做]
在 `.topbar` 左侧添加一个 `☰` 按钮，点击时 toggle `.sidebar` 的显示。
具体实现：
1. 在 `.topbar` 的 HTML 中加入 `<div class="menu-btn" onclick="toggleMobileMenu()">☰</div>`
2. `.menu-btn` 默认 `display:none`，在 `@media(max-width:768px)` 中 `display:block`
3. `toggleMobileMenu()` 函数切换 `.sidebar` 的 `display` 在 `none` 和 `flex` 之间
4. 移动端 `.sidebar` 显示时改为 `position:fixed; top:0; left:0; width:200px; height:100vh; z-index:200`

## Task 4: ECharts resize [建议做]
在 `@media(max-width:768px)` 时触发所有 ECharts 实例 resize。
在 `window.matchMedia('(max-width:768px)')` 变化时调用 `chart.resize()`。

## 验证
- 所有改动通过 `curl -s -o /dev/null -w '%{http_code}' http://localhost:8088/` 返回 200
- PC 端 (>1200px) 布局不变
- 不引入新的 JS 错误
