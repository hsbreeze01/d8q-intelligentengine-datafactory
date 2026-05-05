## ADDED Requirements

### Requirement: Admin can change user role via API
系统 SHALL 提供 `PUT /api/auth/users/<username>/role` 端点，允许 admin 角色修改指定用户的角色。请求 body 必须包含 `role` 字段，值为 `viewer`、`editor` 或 `admin` 之一。

#### Scenario: Admin successfully changes user role
- **WHEN** admin 用户发送 `PUT /api/auth/users/testuser/role`，body 为 `{"role": "editor"}`
- **THEN** 系统 SHALL 更新 `users.json` 中 testuser 的 role 为 "editor"，返回 `{"ok": true, "username": "testuser", "role": "editor"}`

#### Scenario: Non-admin user attempts role change
- **WHEN** 非 admin 用户发送 `PUT /api/auth/users/testuser/role`
- **THEN** 系统 SHALL 返回 403 状态码和 `{"error": "权限不足"}`

#### Scenario: Admin tries to change own role
- **WHEN** admin 用户发送 `PUT /api/auth/users/<自己的用户名>/role`
- **THEN** 系统 SHALL 返回 400 状态码和 `{"error": "不能修改自己的角色"}`

#### Scenario: Invalid role value
- **WHEN** admin 发送 `PUT /api/auth/users/testuser/role`，body 为 `{"role": "superadmin"}`
- **THEN** 系统 SHALL 返回 400 状态码和 `{"error": "无效角色"}`

#### Scenario: Target user not found
- **WHEN** admin 发送 `PUT /api/auth/users/nonexistent/role`
- **THEN** 系统 SHALL 返回 404 状态码和 `{"error": "用户不存在"}`

### Requirement: Role change takes effect on next request
角色变更后，被修改用户的 session SHALL 在下次请求时自动同步为新角色。系统 SHALL 在 `check_auth()` 拦截器中检测 session role 与 users.json 中的 role 是否一致，不一致时更新 session。

#### Scenario: User's session updates after role change
- **WHEN** 用户的 session 中 role 为 "viewer"，但 users.json 中其角色已被 admin 改为 "editor"
- **THEN** 该用户下次请求时，`check_auth()` SHALL 自动将 session["role"] 更新为 "editor"

#### Scenario: User role unchanged
- **WHEN** 用户的 session role 与 users.json 中的 role 一致
- **THEN** `check_auth()` SHALL 不修改 session

### Requirement: Frontend role change UI in settings page
设置页的用户管理表格 SHALL 在每行用户数据旁提供角色变更操作入口。点击后 SHALL 显示包含 viewer/editor/admin 三选项的下拉菜单，选择后 SHALL 弹出确认对话框，确认后调用 API 完成变更并刷新表格。

#### Scenario: Admin changes role via UI
- **WHEN** admin 在用户管理表格点击某用户的"修改角色"按钮，选择 "editor"，并在确认对话框中点击确认
- **THEN** 系统 SHALL 调用 `PUT /api/auth/users/<username>/role`，成功后刷新用户列表，显示新角色

#### Scenario: Admin cancels role change
- **WHEN** admin 在确认对话框中点击取消
- **THEN** 系统 SHALL 不发送任何请求，恢复原始角色显示

#### Scenario: Role change API fails
- **WHEN** 角色变更 API 返回错误
- **THEN** 前端 SHALL 显示错误 Toast 提示，不更新表格中的角色显示
