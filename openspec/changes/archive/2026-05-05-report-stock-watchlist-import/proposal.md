## Why

研报搜索目前只支持单个关键词手动输入，用户需要逐个搜索关注的股票研报，效率低。用户希望能批量导入关注的股票列表（通过 txt 文件），一次性搜索所有关注股票的研报，提升研报跟踪效率。

## What Changes

- 研报搜索区域增加"导入关注列表"功能按钮
- 支持用户上传 txt 文件，文件内每行一个股票名称
- 界面提供文件格式说明和示例提示
- 导入后批量搜索所有股票的研报结果，合并展示
- 支持 txt 文件内容预览和错误提示（空行、格式异常等）

## Capabilities

### New Capabilities
- `stock-watchlist-import`: 研报页面支持通过 txt 文件导入股票名称列表，批量搜索研报

### Modified Capabilities
<!-- 无现有 spec 需要修改 -->

## Impact

- **前端**: `templates/index.html` — 研报搜索区域 UI 改造，增加文件上传、格式提示、批量结果展示
- **后端**: `app.py` — 新增 `/api/report/stock-batch` 代理路由（或复用现有 `/api/report/stock` 扩展 keywords 数组）
- **依赖**: 现有研报搜索 API（`/api/report/stock`）已支持 keywords 数组，无需后端 API 新增
