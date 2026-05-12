# Design: 移动端响应式适配

## 架构决策

### 方案：纯 CSS 补丁 + 最小 JS 改动

选择在现有 `<style>` 末尾追加 `@media(max-width:768px)` 规则块，而非重构 CSS 架构。

**理由：**
- 风险最低：PC 端行为零影响
- 改动集中：仅修改 `templates/index.html` 一个文件
- 无需构建工具：项目是单文件 SPA，无前端构建链

### 已有媒体查询

当前 `index.html` 中已有一条 `@media(max-width:768px)` 规则：
```css
@media(max-width:768px){
  .sidebar{width:56px}
  .sidebar .logo span,.sidebar nav a span,.sidebar .user-box{display:none}
  .sidebar nav a{justify-content:center;padding:12px}
}
```
此规则将被**替换**为完整的移动端响应式规则块。

## 数据流

```
用户浏览器 → viewport width ≤ 768px → @media 规则激活 → 布局重排
                                         ↓
                              汉堡菜单按钮 visible → 用户点击 → sidebar toggle
                                         ↓
                              ECharts 实例 → window.matchMedia 监听 → chart.resize()
```

## 修改文件清单

仅 1 个文件：`templates/index.html`

### 修改区域

1. **`<style>` 末尾（`/* === 资讯 Feed 样式 === */` 之前）**
   - 替换现有 `@media(max-width:768px)` 规则
   - 新增完整移动端 CSS 规则块，覆盖：布局、网格降列、卡片、Feed、详情面板、模态框、汉堡菜单

2. **`.topbar` HTML 区域**
   - 在 `.title` div 之前添加汉堡菜单按钮 `<div class="menu-btn">☰</div>`

3. **JS 区域 — 内联样式修复**
   - 搜索所有 `width:520px`、`width:640px`、`width:500px`、`width:400px` 等硬编码
   - 替换为 `max-width:95vw;width:100%` 写法
   - 搜索 `grid-template-columns:repeat(4,1fr)` 和 `repeat(6,1fr)` 的内联样式，改为 CSS class

4. **JS 区域 — 新增函数**
   - `toggleMobileMenu()` — 切换侧边栏显示
   - ECharts resize 监听器

## CSS 规则设计

```css
@media(max-width:768px) {
  /* 布局 */
  body { flex-direction: column }
  .sidebar { display: none; position:fixed; top:0; left:0; width:200px; height:100vh; z-index:200 }
  .sidebar.mobile-open { display: flex }
  .main { width: 100%; overflow-x: hidden }
  .topbar { padding: 0 12px }
  .topbar .search { width: 120px; font-size: 12px }
  .content { padding: 12px }

  /* 汉堡按钮 */
  .menu-btn { display: flex }

  /* 网格降列 */
  .metrics { grid-template-columns: repeat(2, 1fr) }
  .grid-2 { grid-template-columns: 1fr }
  .sh-metrics { grid-template-columns: repeat(3, 1fr) }
  .rcfg { grid-template-columns: 1fr }

  /* 卡片 */
  .mc .value { font-size: 22px }
  .card { padding: 14px }
  .card h3 { font-size: 14px }

  /* 表格 */
  .et { display: block; overflow-x: auto }

  /* Feed */
  .feed-item { padding: 12px 14px }
  .feed-pager .fp { min-width: 28px; height: 28px; font-size: 11px }

  /* 详情面板 */
  .drawer-panel { width: 100% !important; min-width: 0 !important; max-width: 100vw }

  /* 模态框 */
  #taskModal .card { width: 100% !important; max-width: 95vw !important }
}
```

## JS 内联样式修改清单

以下函数中包含需要修复的硬编码宽度：

| 函数 | 当前值 | 修复后 |
|------|--------|--------|
| `importCookieUI()` | `width:640px` | `max-width:95vw;width:100%` |
| `showCollectForm()` | `width:520px` | `max-width:95vw;width:100%` |
| `showContentForm()` | `width:500px` | `max-width:95vw;width:100%` |
| `showKeywordManager()` | `width:520px` | `max-width:95vw;width:100%` |
| `addMonitorRule()` | `width:500px` | `max-width:95vw;width:100%` |
| `updateCookie()` 选项模式 | `width:520px` | `max-width:95vw;width:100%` |
| `updateCookie()` 扫码模式 | `width:520px` | `max-width:95vw;width:100%` |
| `delUser()` | `width:400px` | `max-width:95vw;width:100%` |
| `resetPw()` | `width:400px` | `max-width:95vw;width:100%` |
| `changeRole()` | `width:400px` | `max-width:95vw;width:100%` |
| `loadSDQuote()` 指标区 | `repeat(4,1fr)` | 使用 class `.tech-indicators` |
| `loadSDTech()` 信号区 | `repeat(4,1fr)` | 使用 class `.tech-signals` |
| `loadValData()` 估值区 | `repeat(4,1fr)` | 使用 class `.val-metrics` |
| `loadStockHeader()` 行情区 | `.sh-metrics` inline | 已有 class，CSS 覆盖即可 |

## 前端任务说明

本 change 的全部任务均为前端 CSS/JS 修改（scope: frontend），位于 `templates/index.html` 单文件中。由于是纯文本代码修改（添加 CSS 规则、替换 JS 字符串），zsiga 可直接执行。
