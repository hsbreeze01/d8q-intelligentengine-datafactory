## Context

D8Q 平台用户数据存储在 `data/users.json`（JSON 文件），角色定义在 `auth.py` 的 `ROLE_PERMS` 字典中（viewer/editor/admin）。当前用户管理 API 支持创建（含角色选择）、删除、冻结、改密码，但**无角色变更接口**。前端 `settings.html` 的用户管理表格展示角色列但不可编辑。

认证机制基于 Flask session，`check_auth()` 拦截器在每次请求时从 `session["role"]` 读取角色并做权限校验。

## Goals / Non-Goals

**Goals:**
- 管理员可在设置页直接修改任意用户的角色，操作即时生效
- 被修改角色的用户无需重新登录即可获得新权限（session 同步）
- 操作有明确的权限校验和防误操作保护

**Non-Goals:**
- 不引入新的角色类型或修改 `ROLE_PERMS` 定义
- 不实现角色变更审计日志（可后续扩展）
- 不修改现有的创建/删除/冻结/改密码功能
- 不考虑分布式 session 同步（当前单实例部署）

## Decisions

### Decision 1: Session 同步策略

**选择**: 角色变更后，在 `check_auth()` 拦截器中对比 session role 与 users.json 中的 role，不一致时自动更新 session。

**理由**:
- 被修改角色的用户可能在其他浏览器有活跃 session
- 直接修改其他用户的 session 在 Flask 中不可行（session 存储在客户端 cookie）
- 懒同步方案：每次请求时检查，角色不一致则更新。对用户透明，无需强制重新登录

**替代方案**: 强制目标用户重新登录（清除其 session）。但 Flask 默认使用客户端 session，无法远程清除其他用户的 cookie。

### Decision 2: API 设计

**选择**: `PUT /api/auth/users/<username>/role`，body 为 `{"role": "editor"}`

**理由**:
- 遵循 RESTful 语义（PUT 更新资源属性）
- 路径与已有的 `PUT /api/auth/users/<username>/password` 保持一致
- 单独端点而非通用 PATCH，减少误操作风险

### Decision 3: 前端交互

**选择**: 用户管理表格的"操作"列增加"修改角色"按钮，点击后弹出下拉选择 + 确认。

**理由**:
- 行内编辑（inline edit）比弹窗更直观
- 需二次确认防止误操作（角色变更直接影响权限）
- 下拉选项直接从 `ROLE_PERMS` 的 key 列表生成（硬编码 viewer/editor/admin 即可）

## Risks / Trade-offs

- **[Session 延迟生效]** → 懒同步方案下，用户下一次请求时才更新 session。如果用户在角色变更瞬间正在执行写操作，可能存在短暂权限不一致。→ 可接受：实际场景中角色变更极少与敏感操作同时发生
- **[误操作风险]** → 管理员可能误改角色 → 前端增加确认弹窗，API 校验角色值合法性
- **[并发写入 users.json]** → 当前 `_save_users` 直接覆盖文件，多请求并发可能丢失 → 已有风险，非本次引入，当前单 worker 部署下无问题
