## Why

当前采集任务列表无法区分"赛道采集"和"自定义（关键词）采集"，用户难以快速识别任务类型。同时，关键词管理的入口放在采集任务行上（每个赛道任务都有"管理关键词"按钮）是不合理的——关键词属于赛道而非任务，同一赛道的多个任务会显示重复的管理按钮，导致概念混淆。

## What Changes

- 采集任务表格增加"类型"列，用 badge 标注"赛道采集"或"自定义采集"
- 移除采集任务行上的"管理关键词"按钮（当前入口）
- 在赛道页面（🔥 赛道）的每个赛道卡片上增加"管理关键词"入口，作为关键词管理的统一入口
- 赛道卡片点击"管理关键词"弹出关键词管理模态框（复用已有的 showKeywordManager）

## Capabilities

### New Capabilities
- `task-type-column`: 采集任务列表增加类型列，区分赛道采集与自定义采集
- `track-page-kw-entry`: 赛道页面的赛道卡片增加关键词管理入口

### Modified Capabilities
- `keyword-management-ui`: 管理入口从任务列表迁移到赛道页面；模态框逻辑不变

## Impact

- **前端**: `templates/index.html` 的 `loadTasks()`（增加类型列、移除管理按钮）和 `loadTrack()`（增加管理入口）
- **后端**: 无变更，已有的代理路由和 data-agent API 完全复用
