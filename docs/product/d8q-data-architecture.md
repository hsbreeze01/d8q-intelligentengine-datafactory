# D8Q 数据架构与用户隔离设计

> 文档版本: v1.0 | 日期: 2026-04-29 | 状态: 需求任务分析
> 前置文档: [高端用户需求规划](./d8q-premium-user-requirements.md) | [交互设计稿](./d8q-interaction-design.md)

---

## 1. 用户数据隔离模型

### 1.1 隔离原则

平台数据分为**全局层**和**用户层**两个维度：

```
全局层（admin 管理）              用户层（per-user）
├── 资讯数据库                    ├── 赛道订阅列表
├── 采集任务配置                  ├── 自选股列表
├── 创作/发布任务                 ├── 我的周报（生成历史）
├── LLM 配置                     ├── 收藏/标记
├── 赛道定义（关键词词典）         ├── 推送配置
└── 用户管理                      └── Dashboard 个性化展示
```

### 1.2 各模块隔离策略

| 模块 | 隔离维度 | 说明 |
|------|----------|------|
| 资讯数据 | 全局共享 | 资讯是公共数据，所有用户看到相同内容 |
| 赛道定义 | 全局（admin 管理） | 赛道名称和关键词由 admin 统一维护 |
| 赛道订阅 | 按用户隔离 | 每人选择关注哪些赛道，影响 Dashboard 和推送 |
| 热度数据 | 全局共享 | 热度指数是客观计算结果，所有人看到相同数据 |
| 自选股 | 按用户隔离 | 每人维护自己的自选股列表 |
| 收藏/标记 | 按用户隔离 | 个人收藏的资讯 |
| 周报 | 按用户隔离 | 每人生成和编辑自己的周报 |
| 推送配置 | 按用户隔离 | 每人配置自己的邮箱、推送类型、时间 |
| 采集任务 | 全局（admin 管理） | 采集是平台级行为，用户只消费数据 |
| 创作/发布任务 | 全局（admin 管理） | 小红书发布等是平台运营行为 |
| LLM 配置 | 全局（admin 管理） | API Key 等全局共享 |

### 1.3 用户维度数据表设计

| 表名 | 核心字段 | 说明 |
|------|----------|------|
| `user_subscriptions` | user_id, track_id, created_at | 用户订阅的赛道 |
| `user_watchlist` | user_id, stock_code, stock_name, created_at | 用户自选股 |
| `user_bookmarks` | user_id, news_id, created_at | 用户收藏的资讯 |
| `weekly_reports` | id, user_id, track_id, date_range, title, content_md, status, created_at | 用户的周报 |
| `push_configs` | user_id, email, enabled_types(JSON), daily_time, weekly_day, alert_threshold, webhook_url | 推送配置 |

---

## 2. 数据分层治理

### 2.1 数据分层总览

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层                                 │
│  Dashboard / 赛道热度 / 资讯流 / 周报 / 个股 / 研报           │
└────────────────────────────┬────────────────────────────────┘
                             │ 读取
┌────────────────────────────▼────────────────────────────────┐
│                        加工层                                 │
│  AI分类 / AI摘要 / NER实体 / 热度聚合 / 周报生成 / 观点提炼   │
└────────────────────────────┬────────────────────────────────┘
                             │ 写入
┌────────────────────────────▼────────────────────────────────┐
│                        存储层                                 │
│  financial_news(扩展) / tracks / track_heat_daily /           │
│  investment_events / weekly_reports / user_* 表               │
└────────────────────────────┬────────────────────────────────┘
                             │ 入库
┌────────────────────────────▼────────────────────────────────┐
│                        采集层                                 │
│  财联社 / 每经 / 36氪 / 政策源 / IT桔子 / 公告源              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 采集层 — 需要爬取的数据

| 数据类型 | 来源 | 用途 | 优先级 | 状态 |
|----------|------|------|--------|------|
| 行业资讯 | 财联社、每经 | 资讯流、热度计算、周报素材 | P0 | ✅ 已有 |
| 科技资讯 | 36氪 | 一级市场动态、融资事件 | P1 | 部分已有 |
| 投融资事件 | 36氪、IT桔子、企查查 | 赛道融资统计、周报"融资与并购"章节 | P1 | ❌ 待新增 |
| 政策文件 | 国务院、发改委、工信部、科技部 | 政策信号监测、政策影响分析 | P1 | ❌ 待新增 |
| 上市公司公告 | 巨潮资讯、东方财富 | 公告智能解读、个股关联资讯 | P2 | ❌ 待新增 |
| 行业研报 | 慧博、东方财富研报中心 | 研报 AI 解读、机构观点提炼 | P2 | StockShark 部分已有 |

### 2.3 加工层 — AI 加工任务

| 加工类型 | 输入 | 输出 | 触发时机 | 优先级 |
|----------|------|------|----------|--------|
| 资讯分类 | title + content | news_type: policy/funding/tech/market/report | 入库时实时 | P0 |
| AI 摘要 | content | 1-2 句话精炼摘要 | 入库时实时 | P0 |
| 实体识别(NER) | title + content | 公司名、人名、产品名 | 入库时实时 | P1 |
| 政策影响分析 | 政策类资讯 | 利好/利空赛道 + 影响程度 | 入库时（仅政策类触发） | P1 |
| 热度评分聚合 | 某赛道某日的资讯量+研报量+政策量 | 综合热度指数 0-100 | 每日定时（凌晨） | P0 |
| 研报观点提炼 | 研报标题+摘要 | 看多/看空/中性 + 核心观点 | 入库时实时 | P1 |
| 周报生成 | 某赛道某时间段的全部数据 | 结构化 Markdown 周报 | 用户手动触发或定时 | P0 |
| 热度异动检测 | 今日热度 vs 昨日热度 | 是否触发推送 | 每日热度聚合后 | P1 |

### 2.4 存储层 — 数据库 Schema

#### 现有表扩展：financial_news

```sql
-- 新增字段（ALTER TABLE）
ALTER TABLE financial_news ADD COLUMN news_type TEXT;        -- policy/funding/tech/market/report
ALTER TABLE financial_news ADD COLUMN ai_summary TEXT;       -- AI 生成摘要
ALTER TABLE financial_news ADD COLUMN entities TEXT;         -- JSON: {"companies":[],"products":[]}
ALTER TABLE financial_news ADD COLUMN heat_weight REAL DEFAULT 1.0;  -- 热度贡献权重
```

#### 新建表

```sql
-- 赛道定义
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- 赛道名称
    keywords TEXT NOT NULL,              -- JSON: ["关键词1","关键词2"]
    color TEXT DEFAULT '#1890ff',        -- 展示颜色
    status TEXT DEFAULT 'active',        -- active/paused
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 每日热度快照
CREATE TABLE track_heat_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    date TEXT NOT NULL,                  -- YYYY-MM-DD
    score REAL NOT NULL,                 -- 热度指数 0-100
    news_count INTEGER DEFAULT 0,
    policy_count INTEGER DEFAULT 0,
    report_count INTEGER DEFAULT 0,
    funding_count INTEGER DEFAULT 0,
    UNIQUE(track_id, date)
);

-- 投融资事件
CREATE TABLE investment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    round TEXT,                          -- 天使/A/B/C/IPO
    amount TEXT,                         -- "1.1亿美元"
    investors TEXT,                      -- JSON: ["投资方1","投资方2"]
    track_id INTEGER,
    event_date TEXT,
    source_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户赛道订阅
CREATE TABLE user_subscriptions (
    user_id TEXT NOT NULL,
    track_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, track_id)
);

-- 用户自选股
CREATE TABLE user_watchlist (
    user_id TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, stock_code)
);

-- 用户收藏
CREATE TABLE user_bookmarks (
    user_id TEXT NOT NULL,
    news_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, news_id)
);

-- 周报
CREATE TABLE weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    track_id INTEGER,
    title TEXT,
    date_from TEXT,                      -- 周报覆盖起始日期
    date_to TEXT,                        -- 周报覆盖结束日期
    template TEXT DEFAULT 'standard',    -- standard/committee/lp_brief
    content_md TEXT,                     -- Markdown 内容
    status TEXT DEFAULT 'draft',         -- draft/final
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 推送配置
CREATE TABLE push_configs (
    user_id TEXT PRIMARY KEY,
    email TEXT,
    enabled_types TEXT DEFAULT '[]',     -- JSON: ["daily_brief","weekly_report","heat_alert"]
    daily_time TEXT DEFAULT '08:00',
    weekly_day TEXT DEFAULT 'friday',
    alert_threshold INTEGER DEFAULT 30,  -- 热度涨幅阈值%
    webhook_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.5 现有数据元数据重构

当前 `financial_news` 表存量 390 条数据的问题与修复：

| 字段 | 问题 | 修复方案 |
|------|------|----------|
| `category` | 全部是"技术"，无实际分类价值 | LLM 重新分类，写入新字段 `news_type` |
| `subject` | 命名不统一："AI"和"人工智能"重复，"先进材料"和"碳纤维"层级混乱 | 统一标准化，建立 `tracks` 表作为权威词典 |
| `content` | 每经内容含大量 HTML 残留、免责声明、导航链接噪音 | 清洗脚本去除噪音 |
| `metadata` | Schema 有但数据全为空 | 用于存储扩展信息（可选） |
| `ai_summary` | 不存在 | LLM 批量回填 |
| `news_type` | 不存在 | LLM 批量回填 |
| `entities` | 不存在 | LLM 批量回填 |

**存量迁移步骤：**

| 步骤 | 操作 | 耗时 |
|------|------|------|
| 1 | ALTER TABLE 新增字段 | 1 分钟 |
| 2 | `subject` 标准化（"AI"→"人工智能"，"先进材料"→"新材料"） | 脚本 10 分钟 |
| 3 | `content` 清洗（去 HTML/免责声明/导航） | 脚本 30 分钟 |
| 4 | `news_type` 回填（LLM 批量分类） | ~20 分钟 |
| 5 | `ai_summary` 回填（LLM 批量摘要） | ~40 分钟 |
| 6 | `entities` 回填（LLM 批量 NER） | ~30 分钟 |
| 7 | 创建 `tracks` 表并初始化赛道数据 | 5 分钟 |
| 8 | 基于历史 publish_time 回填 `track_heat_daily` | 脚本 5 分钟 |

**总计约 2 小时完成存量重构。**

---

## 3. 推送服务设计

### 3.1 推送内容类型

| 类型 | 触发方式 | 内容 | 频率 |
|------|----------|------|------|
| 每日早报 | 定时（用户配置时间，默认 08:00） | 赛道热度概览 + TOP5 要闻摘要 | 每日 |
| 周报推送 | 定时（每周五）或手动生成后 | 用户生成的周报全文 | 每周 |
| 热度异动 | 事件驱动（涨幅超阈值） | 赛道名 + 涨幅 + 关键事件 | 实时 |
| 政策预警 | 事件驱动（检测到政策类资讯） | 政策标题 + AI 影响分析 | 实时 |

### 3.2 推送渠道

| 渠道 | 优先级 | 实现难度 | 成本 | 适合场景 |
|------|--------|----------|------|----------|
| 邮件（SMTP） | P0 先做 | 低 | 免费（QQ/163 邮箱 SMTP） | 周报、早报（长内容） |
| 微信服务号 | P1 | 中 | 需申请服务号 | 异动提醒（短通知） |
| 企微/飞书 Webhook | P2 | 低 | 免费 | 团队协作场景 |

### 3.3 架构

```
触发源                      推送服务                    渠道

调度器 (每日 08:00) ──┐     ┌────────────────────┐    ┌→ SMTP → 邮箱
                      │     │                    │    │
调度器 (每周五) ─────┤──→  │  push_service.py   │──→─┤
                      │     │                    │    │
热度聚合完成 hook ───┤     │  - render(type)    │    └→ Webhook (可选)
                      │     │  - send(channel)   │
资讯入库 hook ───────┘     │  - log(result)     │
(政策类触发)                └────────────────────┘
                                    │
                             push_configs 表
                             (per-user 配置)
```

### 3.4 实现方案

- **不搭建邮件服务器**，直接使用现有邮箱的 SMTP 服务
- 种子期用 QQ/163 邮箱 SMTP（免费，每日 ~200 封，10-20 人足够）
- 规模化后切换企业邮箱或阿里云邮件推送服务
- SMTP 配置通过环境变量注入（`SMTP_HOST`、`SMTP_USER`、`SMTP_PASS`）
- 不引入消息队列，同步发送，失败记录日志

### 3.5 站内通知

**当前阶段不做站内信。** 原因：
- 种子用户不会主动打开网站看通知
- 核心问题是"把用户拉回来"，靠外部推送解决
- Dashboard 的"待处理"指标卡已承担"进来后看状态"的功能

待日活 >100 或有团队协作需求时再评估。

---

## 4. 工程改动范围

### 4.1 各工程职责与改动量

| 工程 | 职责 | 本次改动量 | 说明 |
|------|------|------------|------|
| d8q-data-agent | 数据采集 + 存储 | **大** | Schema 扩展、AI 加工管道、新数据源、热度聚合、API 扩展 |
| d8q-factory | 内容加工 + 展示 + 调度 | **最大** | 前端全面重构、用户维度表、周报引擎、推送服务、后端 API |
| d8q-stockshark | 个股/研报分析 | **无** | 维持现有 API，Factory 继续调用 |
| d8q-infopublisher | 小红书发布 | **无** | 维持现有能力，后续 Wyse 替换独立排期 |

### 4.2 d8q-data-agent 改动清单

| 改动项 | 工作量 |
|--------|--------|
| 数据库 Schema 扩展（ALTER + 新建表） | 0.5 天 |
| 存量数据迁移脚本 | 1 天 |
| 采集管道增加 AI 加工步骤（分类+摘要+NER） | 2 天 |
| 新增数据源适配器（投融资、政策） | 3 天 |
| 热度聚合定时任务 | 1 天 |
| API 扩展（热度查询、赛道筛选、实体搜索） | 2 天 |
| **小计** | **~10 天** |

### 4.3 d8q-factory 改动清单

| 改动项 | 工作量 |
|--------|--------|
| 前端全面重构（侧边栏 + 8 页面） | 5 天 |
| 新增页面: Dashboard | 2 天 |
| 新增页面: 赛道热度 | 3 天 |
| 新增页面: 周报工作台 | 5 天 |
| 资讯页/研报页/个股页重构 | 5 天 |
| 设置页扩展（赛道管理+推送配置） | 1 天 |
| 用户维度数据表 + API | 2 天 |
| 周报生成引擎（多模板） | 3 天 |
| 推送服务（邮件） | 2 天 |
| 调度器扩展（早报+异动检测） | 1 天 |
| **小计** | **~29 天** |

### 4.4 实施顺序

```
Week 1-2:  d8q-data-agent 改造
             Schema 扩展 → 存量迁移 → AI 加工管道 → 热度聚合
             ↓ 数据层就绪

Week 2-3:  d8q-factory 后端
             用户维度表 → 赛道/热度/周报/收藏 API → 推送服务
             ↓ 接口就绪

Week 3-5:  d8q-factory 前端
             侧边栏布局 → Dashboard → 赛道页 → 周报工作台
             ↓ 核心功能可用

Week 5-6:  收尾
             资讯页/研报页/个股页重构 → 推送配置 → 联调测试
             ↓ 全站完成

Week 6:    种子用户邀请试用
```

---

## 5. 技术决策

| 决策点 | 结论 | 原因 |
|--------|------|------|
| 数据库 | 继续 SQLite，暂不迁 PostgreSQL | 种子用户 10-20 人，SQLite 够用 |
| 前端框架 | 继续原生 HTML+JS，不引入 Vue/React | 页面不多，避免构建工具复杂度 |
| 图表库 | ECharts（CDN 引入） | 金融图表能力强，无需构建 |
| 富文本编辑器 | Quill 或 Tiptap（CDN） | 轻量，Markdown 友好 |
| 周报导出 | WeasyPrint(PDF) + python-docx(Word) | Python 生态，服务端生成 |
| 邮件发送 | SMTP（QQ/163 邮箱） | 免费，零搭建成本 |
| 消息队列 | 不引入 | 用户量小，同步发送即可 |

---

*本文档为数据架构与用户隔离的需求任务分析，作为后续开发实施的技术输入。*
