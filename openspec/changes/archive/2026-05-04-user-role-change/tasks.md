## 1. 后端 API

- [x] 1.1 在 `auth.py` 新增 `PUT /api/auth/users/<username>/role` 路由：接收 `{"role": "viewer|editor|admin"}`，校验当前用户为 admin、不能修改自己、角色值合法、目标用户存在，更新 `users.json` 并返回 `{"ok": true, "username": "...", "role": "..."}`
- [x] 1.2 在 `check_auth()` 拦截器中增加 session role 懒同步逻辑：当 session 中有 username 时，从 users.json 读取该用户的实际 role，与 session["role"] 不一致则更新 session["role"]

## 2. 前端 UI

- [x] 2.1 在 `settings.html` 用户管理表格的"操作"列增加"修改角色"按钮，点击后将当前角色文字替换为 `<select>` 下拉菜单（viewer/editor/admin 三个选项，默认选中当前角色）
- [x] 2.2 选择新角色后弹出确认对话框（`confirm("确认将用户 XXX 的角色从 YYY 改为 ZZZ？")`），确认后调用 `PUT /api/auth/users/<username>/role`，成功则刷新用户列表并显示成功 Toast，失败则显示错误 Toast 并恢复原始角色显示

## 3. 验证

- [x] 3.1 手动测试：admin 修改其他用户角色 → 被修改用户刷新页面后权限立即变化（viewer 无法看到任务页 → editor 升级后可见）
- [x] 3.2 手动测试异常场景：非 admin 调用返回 403、修改自己返回 400、无效角色返回 400、不存在用户返回 404
