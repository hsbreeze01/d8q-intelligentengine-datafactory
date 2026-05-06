## ADDED Requirements

### R1: 运营分析看板入口

**Given** 管理员登录系统
**When** 进入设置页面
**Then** 可见第 4 个子 Tab "📊 运营分析"（排在"用户管理"之后）

- 仅 admin 角色可见
- 点击切换到运营分析视图

### R2: 功能使用排行

**Given** 运营分析看板已加载
**When** 查看功能排行区域
**Then** 显示水平柱状图，列出所有功能按使用次数降序排列

- 展示：功能名称、使用次数、使用占比
- 支持选择时间范围：近 7 天 / 30 天 / 全部
- 使用 ECharts 水平柱状图渲染

### R3: 活跃度趋势

**Given** 运营分析看板已加载
**When** 查看趋势区域
**Then** 显示折线图，X 轴为日期，Y 轴为活跃用户数和总 API 调用数

- 双 Y 轴：左轴 DAU，右轴总调用量
- 默认展示近 30 天
- 可切换到近 7 天

### R4: 用户活跃度排名

**Given** 运营分析看板已加载
**When** 查看用户区域
**Then** 显示表格：用户名、最近活跃时间、使用功能数、总调用次数、日均调用

- 按总调用次数降序
- 标注不活跃用户（7天未使用）

### R5: 功能冷热图

**Given** 运营分析看板已加载
**When** 查看冷热图区域
**Then** 显示用户×功能矩阵，格子颜色深浅表示使用频次

- 行 = 用户名，列 = 功能名称
- 格子数值 = 该用户对该功能的使用次数
- 颜色梯度：白色（0次）→ 浅蓝 → 深蓝（高频）
- 未使用的功能标红提示

### R6: 总览指标卡片

**Given** 运营分析看板已加载
**When** 查看顶部区域
**Then** 显示 4 个指标卡片：

1. 今日活跃用户（DAU）
2. 本月活跃用户（MAU）
3. 今日总事件数
4. 最热门功能名称 + 次数

### R7: 聚合查询 API

**Given** 管理员已登录
**When** 调用 `/api/analytics/*` 端点
**Then** 返回对应的聚合分析数据

- `GET /api/analytics/overview` → {dau, mau, today_events, top_function}
- `GET /api/analytics/functions?days=30` → [{function_name, count, percentage}]
- `GET /api/analytics/users?days=30` → [{user_id, last_active, function_count, total_calls, daily_avg}]
- `GET /api/analytics/trends?days=30` → [{date, dau, total_calls}]
- `GET /api/analytics/cold-hot?days=30` → {users: [], functions: [], matrix: [[count]]}
- 非管理员调用返回 403
