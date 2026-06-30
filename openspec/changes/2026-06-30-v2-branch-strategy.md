# V2.0 分支策略与数据兼容性规范

## 分支结构

```
main (稳定发布)
  └── premium (当前生产环境运行版本)
        └── junior-assistant (V2.0开发分支)
```

## 各仓库分支状态

| 仓库 | 服务器 | 原分支 | 新分支 | 说明 |
|------|--------|--------|--------|------|
| d8q-intelligentengine-datafactory | 47.99.57.152 | premium | junior-assistant | Factory前后端 |
| d8q-data-agent | 47.99.57.152 | premium | junior-assistant | 数据Agent |
| d8q-intelligentengine-stockcompass | 47.99.57.152 | premium | junior-assistant | 股票罗盘 |
| d8q-intelligentengine-stockshark | 49.234.48.221 | premium | junior-assistant | 行情分析 |
| d8q-intelligentengine-infopublisher | 49.234.48.221 | premium | junior-assistant | 信息发布 |

## 开发规范

1. 所有V2.0功能在 junior-assistant 分支开发
2. 开发完成后合并回 premium 进行集成测试
3. 测试通过后 premium 合并到 main 作为正式发布
4. junior-assistant 可随时从 premium rebase 获取紧急修复

## 数据建模向前兼容规范

### 原则

- **只增不删**: 新增表和字段，不修改/删除现有表结构
- **默认值兜底**: 新增字段必须有 DEFAULT 值，确保旧代码写入不报错
- **NULL友好**: 新增字段允许 NULL，旧代码不感知新字段
- **读兼容**: 旧版本代码读取时忽略新字段，不会crash
- **写兼容**: 旧版本代码写入时新字段取DEFAULT/NULL

### 新增表（无兼容风险）

| 表名 | 所属模块 | 所在服务 | 数据库文件 |
|------|----------|----------|-----------|
| alert_rules | 预警中心 | Factory | financial_news.db |
| alerts | 预警中心 | Factory | financial_news.db |
| score_history | 自选股日报 | Factory | financial_news.db |
| portfolios | 虚拟组合 | Factory | financial_news.db |
| positions | 虚拟组合 | Factory | financial_news.db |
| trades | 虚拟组合 | Factory | financial_news.db |
| recommendation_results | 推荐回溯 | Shark | shark.db |
| followed_investors | 投融资增强 | Factory | financial_news.db |

### DDL创建策略

所有建表使用 `CREATE TABLE IF NOT EXISTS`，确保：
- 服务重启时幂等创建
- premium 分支回滚时不影响现有表
- 多次部署不重复创建

示例:
```sql
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    rule_id INTEGER,
    alert_type TEXT NOT NULL,
    severity TEXT DEFAULT 'normal',
    title TEXT NOT NULL,
    message TEXT,
    context_json TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alerts_user_unread
    ON alerts(user_id, is_read, created_at DESC);
```

### 索引策略

所有索引使用 `CREATE INDEX IF NOT EXISTS`，命名规范：
- `idx_{表名}_{字段名1}_{字段名2}`
- 联合索引字段按查询频率排序

### 数据迁移（如需修改现有表）

如果未来需要修改现有表结构：
1. 使用 `ALTER TABLE ADD COLUMN`（SQLite支持）
2. 新列必须有 DEFAULT 值
3. 不使用 DROP COLUMN（SQLite 3.35+ 才支持，生产环境版本不确定）
4. 不使用 RENAME COLUMN（避免旧代码引用失败）
5. 必要时用 migration 脚本：创建新表 → 复制数据 → 删除旧表 → 重命名

### 回滚方案

如果 junior-assistant 需要回滚到 premium：

| 层面 | 操作 | 影响 |
|------|------|------|
| 代码 | `git checkout premium && systemctl restart` | 立即生效 |
| 数据 | 新增的表不删除（不影响旧代码） | orphan数据保留 |
| 配置 | 无配置变更 | 所有新功能通过代码判断 |
| API | 新路由不存在但前端也不请求 | 无影响 |

### API兼容规范

- 新增API路径不与现有冲突（使用 /api/alerts, /api/portfolios 等新namespace）
- 现有API的响应格式不变，如需扩展只增加新字段（向后兼容）
- 前端通过 loadPage 机制隔离，新增page不影响现有page
- 代理API使用独立Blueprint（investment_api.py），可单独disable

### Feature Flag（可选）

对于渐进式发布，可在 settings 表增加 feature flag：
```python
FEATURES = {
    'alert_center': True,
    'watchlist_daily': True,
    'portfolio_sim': False,  # 开发中暂不开放
    'rec_backtrack': False,
}
```

PAGES 渲染时根据 flag 决定是否显示入口。
