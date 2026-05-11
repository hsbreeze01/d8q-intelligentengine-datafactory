# Spec: 移动端响应式适配

## ADDED Requirements

### Requirement: 移动端视口布局适配

当浏览器视口宽度在 390px-768px 之间时，页面 SHALL 重新排列布局使所有内容可见且可操作：

- 侧边栏 SHALL 完全隐藏，改为通过汉堡菜单按钮切换显示
- 主内容区 SHALL 占满视口宽度，禁用水平滚动
- 顶部导航栏 SHALL 缩减内边距，搜索框 SHALL 收窄至 120px
- 内容区 padding SHALL 缩减至 12px

#### Scenario: 手机浏览器访问首页

```
Given 用户使用 iPhone 14 (390×844) 浏览器访问平台
When 页面完成加载
Then 侧边栏不可见
And 顶部导航栏左侧显示 ☰ 汉堡菜单按钮
And 主内容区宽度等于视口宽度
And 无水平滚动条
```

#### Scenario: PC 端访问不受影响

```
Given 用户使用桌面浏览器 (1920×1080) 访问平台
When 页面完成加载
Then 侧边栏以 200px 宽度正常显示
And 布局与改动前完全一致
```

### Requirement: 网格组件列数降级

移动端下，多列网格 SHALL 自动降列以避免内容挤压溢出：

- 概览页指标卡片从 4 列降为 2 列
- 双栏图表区从 `1.5fr 1fr` 降为单列堆叠
- 个股详情 6 列指标区降为 3 列
- 周报配置 3 列网格降为单列
- 技术指标信号区从 4 列降为 2 列
- 估值数据 4 列指标降为 2 列

#### Scenario: 概览页指标卡片在手机上可读

```
Given 用户在 390px 宽度下查看概览页
When 4 个指标卡片渲染完成
Then 卡片以 2×2 网格排列
And 每张卡片内数字 font-size 不超过 22px
And 第 4 个卡片完全可见，无溢出
```

#### Scenario: 图表区域不溢出

```
Given 用户在 390px 宽度下查看含 ECharts 图表的页面
When 图表容器渲染完成
Then 图表容器为单列全宽
And ECharts 实例自动 resize 适配容器宽度
```

### Requirement: 移动端模态框与详情面板适配

所有弹出层在移动端 SHALL 限制在视口范围内：

- 模态框 SHALL 使用 `max-width:95vw; width:100%` 替代固定像素宽度
- 详情面板（drawer）在移动端 SHALL 全屏覆盖
- 分页器按钮 SHALL 缩小尺寸防止溢出

#### Scenario: 新建采集任务模态框在手机上可用

```
Given 用户在 390px 宽度下点击"新建采集任务"
When 模态框弹出
Then 模态框宽度不超过视口的 95%
And 所有表单字段可见且可交互
And 无内容溢出屏幕
```

#### Scenario: 股票详情面板在手机上全屏展示

```
Given 用户在 390px 宽度下点击某只股票
When 右侧详情面板滑出
Then 面板覆盖整个视口 (position:fixed; inset:0)
And 面板内所有 tab 内容可滚动查看
```

### Requirement: 汉堡菜单导航

移动端 SHALL 提供汉堡菜单按钮替代侧边栏导航：

- 按钮在 768px 以上隐藏，768px 以下显示
- 点击按钮切换侧边栏在 `display:none` 和 `display:flex` 之间
- 侧边栏展开时以 fixed 浮层形式覆盖内容区
- 点击导航项后自动收起侧边栏

#### Scenario: 手机端通过汉堡菜单切换页面

```
Given 用户在 390px 宽度下查看平台
When 用户点击顶部 ☰ 按钮
Then 侧边栏以 fixed 浮层 (width:200px; height:100vh) 从左侧展开
When 用户点击"资讯"导航项
Then 页面切换到资讯页
And 侧边栏自动收起
```

### Requirement: JS 内联样式响应式修复

所有 JavaScript 动态生成 HTML 中的硬编码像素宽度 SHALL 改为响应式写法：

- `width:520px`、`width:640px`、`width:680px`、`width:700px` 等内联样式 SHALL 替换为 `max-width:95vw;width:100%` 或等效写法
- JS 内联 `grid-template-columns:repeat(4,1fr)` 和 `repeat(6,1fr)` SHALL 改为使用 CSS class 以便响应式规则覆盖

#### Scenario: Cookie 导入对话框在手机上不溢出

```
Given 用户在 390px 宽度下打开 Cookie 导入对话框
When 对话框渲染完成
Then 对话框宽度不超过视口 95%
And 粘贴区域和按钮可见可用
```

#### Scenario: 技术指标信号区在手机上 2 列显示

```
Given 用户在 390px 宽度下查看个股技术分析页
When 技术信号区域渲染完成
Then 信号卡片以 2 列网格排列
And 每张卡片文字可读
```

### Requirement: ECharts 图表自适应

移动端下所有 ECharts 实例 SHALL 自动 resize 适配容器宽度：

- 页面加载时若视口 ≤768px，所有 chart 实例触发 resize
- 媒体查询变化时触发 resize
- 侧边栏切换时触发 resize

#### Scenario: 窗口旋转后图表自适应

```
Given 用户在手机上查看含图表的页面
When 用户将手机从竖屏旋转到横屏
Then 所有 ECharts 图表自动 resize 适配新宽度
```
