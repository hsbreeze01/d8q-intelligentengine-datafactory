## 1. Factory 后端代理路由

- [x] 1.1 在 `app.py` 中添加 `POST /api/proxy/tracks/<int:track_id>/keywords` 代理路由，转发到 data-agent
- [x] 1.2 在 `app.py` 中添加 `DELETE /api/proxy/tracks/<int:track_id>/keywords/<path:keyword>` 代理路由，转发到 data-agent
- [x] 1.3 验证两条代理路由通过 curl 调用正常工作

## 2. 前端管理入口

- [x] 2.1 在 `index.html` 的 `loadTasks()` 中，为有 track_id 的任务行添加"管理关键词"按钮
- [x] 2.2 新增 `showKeywordManager(trackId, trackName)` 函数，弹出关键词管理模态框
- [x] 2.3 模态框中调用 `GET /api/proxy/tracks/{id}/keywords` 加载并展示已有关键词标签列表
- [x] 2.4 每个关键词标签带删除按钮，点击调用 `DELETE /api/proxy/tracks/{id}/keywords/{keyword}` 并刷新列表

## 3. 前端添加关键词

- [x] 3.1 模态框底部添加输入框 + "添加"按钮
- [x] 3.2 输入为空时显示"关键词不能为空"提示，不发送请求
- [x] 3.3 输入非空时调用 `POST /api/proxy/tracks/{id}/keywords`，成功后刷新关键词列表
- [x] 3.4 后端返回重复关键词错误时，前端显示"关键词已存在"提示

## 4. 集成验证

- [x] 4.1 部署到服务器，重启 factory 服务
- [x] 4.2 在 UI 中测试：打开赛道任务的关键词管理、添加新关键词、删除关键词
- [x] 4.3 提交并推送代码变更
