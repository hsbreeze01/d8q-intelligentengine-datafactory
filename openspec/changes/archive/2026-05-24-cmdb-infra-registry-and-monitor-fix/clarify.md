# Clarify: CMDB Infrastructure Registry and Monitor Fix

## 需求拆解

### 原始需求
建立 CMDB 基础设施注册表（infra_assets 表），统一管理 D8Q 多机部署的服务资产信息；修复 monitor_rules 初始化失败导致监控规则为空的问题；将服务健康检测从硬编码 IP 改为 CMDB 驱动。

### 拆解后的子任务

- [ ] 1. **infra_assets 表设计与初始化** — 在 `_init_monitor_tables()` 附近新增 `_init_infra_assets()` 函数，创建 infra_assets 表（id, name, host, port, health_path, service_type, group_name, env, enabled, metadata_json, created_at, updated_at），并在表为空时插入 7 条 builtin 服务记录（factory, agent, compass, stockshark, infopublisher, ghost_browser, mysql）。在 app.py 启动时调用。（预估复杂度：中, 预估 token：~4000 / 无历史参考）

- [ ] 2. **monitor_rules 初始化修复** — 排查 `_init_monitor_tables()` 中 builtin_rules 未插入的根因（DB 文件权限 / 首次启动顺序 / 异常静默吞没），修复后确保重启自动填充 4 条内置规则；将规则 config_json 中硬编码的 PUBLISHER_API + host 改为从 infra_assets 表动态查询。（预估复杂度：中, 预估 token：~5000 / 无历史参考）

- [ ] 3. **service_status API 改造** — 重写 `/api/service-status` 路由，从 infra_assets 表动态读取服务列表，按 service_type（http/cdp/db/systemd）分别执行健康检测；保持原有返回 JSON 格式兼容（服务名、状态、latency_ms、detail）。（预估复杂度：中, 预估 token：~6000 / 无历史参考）

- [ ] 4. **Ghost Browser 检测路径优化** — 将 Ghost Browser 健康检测从 `localhost:9222`（SSH 隧道）改为直接检测 `49.234.48.221:9222`，通过 infra_assets 表中 service_type=cdp 配置实现；monitor_rules 中对应 builtin 规则同步更新。（预估复杂度：低, 预估 token：~2000 / 无历史参考）

- [ ] 5. **单元测试与验证** — 编写测试验证：infra_assets 表创建与 builtin 数据插入、monitor_rules builtin 规则填充、service_status API 返回格式兼容性、Ghost Browser 直接检测路径正确性。（预估复杂度：中, 预估 token：~4000 / 无历史参考）

## 边界

### IN scope
- 新建 infra_assets 表及 builtin 数据初始化
- 修复 monitor_rules builtin 规则未插入问题
- monitor_rules config_json 中硬编码 URL 改为 CMDB 查询驱动
- service_status API 从 infra_assets 动态读取服务列表
- Ghost Browser 检测从 localhost:9222 改为 49.234.48.221:9222
- 保持 /api/service-status 返回格式向后兼容
- 单元测试覆盖上述改动

### OUT of scope
- 清理 47 上残留的 SSH tunnel / Chrome 进程（仅记录到 learnings）
- infra_assets 的 CRUD 管理 UI 或 API（后续迭代）
- 非 factory 项目中的改动（agent/compass/stockshark/shark 侧）
- monitor_rules 表结构变更
- 新增监控规则类型

### 依赖的外部条件
- SQLite DB 文件（data/ 目录）可写
- 49.234.48.221:9222 Ghost Browser CDP 端口从 factory 网络可达
- 现有服务健康端点保持可用（/api/health, /health, /json/version）

## 目标

### 成功标准
1. app.py 启动后 infra_assets 表存在且包含 7 条 builtin 服务记录
2. monitor_rules 表自动填充 4 条内置规则，config_json 中无硬编码 IP
3. GET /api/service-status 返回格式与现有前端兼容，数据来源为 infra_assets 动态查询
4. Ghost Browser 通过 49.234.48.221:9222 直接检测（非 SSH 隧道）
5. 所有新增/修改通过 pytest + ruff check

### 验收方式
- 启动 app.py 后查询 infra_assets 表确认 7 条 builtin 数据
- 查询 monitor_rules 表确认 4 条 builtin 规则存在
- curl /api/service-status 验证返回格式与迁移前一致
- ruff check + pytest 全部通过
- 检查 monitor_rules config_json 无硬编码 49.234.48.221 或 PUBLISHER_API 字面量

## 约束

### 不能修改的文件
- templates/ 目录下所有前端模板文件（service_status 页面渲染逻辑不变）
- src/datafactory/ 下除 infrastructure/db_utils.py 外的模块
- auth.py, compass_pages.py, export_weekly.py（非本次改动范围）

### 项目部署分支
- main

### 已知风险
- SQLite DB 文件权限问题可能导致表创建失败（需在 _init 中增加日志和错误处理）
- 47→49 迁移后 47 上残留进程可能导致 localhost:9222 端口冲突（本次不清理，仅记录）
- service_status API 改造需确保 cdp 类型检测的超时处理稳健，避免拖慢整体响应
- monitor_rules config_json 中 PUBLISHER_API 常量在初始化时解析，需确保 infra_assets 先于 monitor_rules 初始化

### 预估 token 消耗
- prompt: ~21000
- completion: ~8000
- 数据来源: 无历史参考
