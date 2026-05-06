## Why

D8Q 平台的用户管理系统支持创建用户时选择角色（viewer/editor/admin），但**创建后无法修改角色**。管理员当前只能冻结或删除用户，无法将 viewer 升级为 editor 或降级 admin。随着平台用户增长（已有 9+ 账号），角色调整需求频繁出现——新同事入职需从 viewer 升为 editor、权限回收需降级、测试账号需临时提权等。缺少角色变更功能迫使管理员只能"删了重建"，丢失用户关联数据（订阅、自选股、书签）。

## What Changes

- 新增 `PUT /api/auth/users/<username>/role` API，允许 admin 修改任意用户的角色
- 在角色变更后即时更新目标用户的 session，使其无需重新登录即可获得新权限
- 前端设置页用户管理表格增加角色变更交互（行内下拉选择 + 确认）
- 角色变更有操作校验：不能修改自己的角色、角色值必须在 viewer/editor/admin 范围内

## Capabilities

### New Capabilities
- `user-role-update`: 用户角色变更 API 及前端交互——管理员在用户管理界面修改指定用户的角色，含权限校验、session 同步、操作反馈

### Modified Capabilities

## Impact

- **后端 `auth.py`**：新增 1 个 API 路由（`PUT /api/auth/users/<username>/role`），修改 `_load_users`/`_save_users` 已有逻辑无变动
- **前端 `settings.html`**：用户管理表格"操作"列增加角色变更下拉菜单和确认逻辑
- **Session 同步**：需考虑被修改角色的用户可能在其他设备有活跃 session，变更需立即生效（或下次请求时生效）
- **兼容性**：不影响现有创建/删除/冻结/改密码功能；内部 IP 调用不受影响
