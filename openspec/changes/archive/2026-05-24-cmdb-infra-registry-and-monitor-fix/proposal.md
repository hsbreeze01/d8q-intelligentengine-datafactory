# Proposal: CMDB Infrastructure Registry and Monitor Fix

## Summary

建立 CMDB 基础设施注册表（infra_assets 表），统一管理 D8Q 多机部署的服务资产信息；修复 monitor_rules 初始化失败导致监控规则为空的问题；将服务健康检测从硬编码 IP 改为 CMDB 驱动。

## Motivation

D8Q 已完成 StockShark 和 InfoPublisher 从 47.99.57.152 到 49.234.48.221 的迁移，当前状态：

1. **service_status API**：host 地址硬编码在 app.py 第 1087/1090 行（49.234.48.221），Ghost Browser 通过 SSH 隧道 localhost:9222 检测
2. **monitor_rules 表为空**：_init_monitor_tables() 初始化代码存在但 builtin_rules 未插入（可能是 DB 文件权限或首次启动顺序问题）
3. **无 CMDB 表**：服务资产信息散落在代码硬编码中（SHARK_API、PUBLISHER_API 等常量），无法动态管理
4. **Ghost Browser 检测依赖 SSH 隧道**：47 上有残留的 Chrome 进程 + SSH tunnel 转发 49 的 9222 端口，架构脆弱

## Expected Behavior

### 1. CMDB infra_assets 表
新建 infra_assets 表，字段：
- id, name (服务名), host (IP), port, health_path, service_type (http/cdp/db/systemd), group_name (d8q/zsiga), env (production/staging), enabled, metadata_json, created_at, updated_at

初始数据（builtin）：
- factory: localhost:8088, /
- agent: localhost:8000, /api/health
- compass: localhost:8087, /health
- stockshark: 49.234.48.221:5000, /health
- infopublisher: 49.234.48.221:8089, /api/health
- ghost_browser: 49.234.48.221:9222, /json/version (type=cdp)
- mysql: localhost:3306 (type=db)

### 2. monitor_rules 初始化修复
- 检查 _init_monitor_tables() 为什么没有插入 builtin_rules
- 修复后确保重启时自动填充 4 条内置规则
- 将规则中的 PUBLISHER_API 硬编码改为从 infra_assets 查询

### 3. service_status API 改造
- 从 infra_assets 表动态读取服务列表
- 不再硬编码 host/port
- 支持 cdp 类型服务通过 host:port 直接检测（不再依赖 SSH 隧道）

### 4. Ghost Browser 检测优化
- 直接检测 49.234.48.221:9222（不再走 SSH 隧道 localhost:9222）
- 如 47 上残留的 SSH tunnel 和 Chrome 进程不再需要，记录到 learnings

## Constraints

- 不修改现有 API 的返回格式（/api/service-status 保持兼容）
- monitor_rules 表结构不变
- 所有改动在 factory 项目中
- SQLite 数据库存放在 data/ 目录
