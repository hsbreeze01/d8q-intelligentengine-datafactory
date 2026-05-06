## Context

系统现有 5 个赛道，存储在 `d8q-data-agent/data/financial_news.db` 的 `tracks` 表（id, name, keywords, color, status, created_at）。关键词存储在 `d8q-data-agent/data/task_store.db` 的 `track_keywords` 表（id, track_name, keyword, UNIQUE(track_name, keyword)）。

tracks 表的 `keywords` 字段是 JSON 数组，用于前端展示；track_keywords 表是实际采集时使用的关键词列表。两者需同步维护。

## Goals / Non-Goals

**Goals:**
- 新增"量子计算"赛道，关键词覆盖量子科技三大产业 + 底层支撑 + 产业落地
- 中英文关键词兼备，确保国内外资讯都能命中

**Non-Goals:**
- 不修改赛道管理 API 或前端代码
- 不影响现有赛道的运行

## Decisions

### 1. 赛道名称："量子计算"

**选择**：赛道名用"量子计算"而非"量子科技"。

**理由**：用户明确指定赛道名为"量子计算"。虽然关键词覆盖范围更广（含通信、测量），但赛道名保持简洁聚焦。

### 2. 关键词体系设计

基于用户反馈"三大产业 + 底层支撑 + 交叉应用"，构建 5 个维度的关键词：

| 维度 | 中文关键词 | 英文关键词 |
|---|---|---|
| 量子计算 | 量子计算、量子芯片、量子比特、超导量子、离子阱、光量子、量子纠错、量子退相干、量子门、量子霸权 | quantum computing, qubit, superconducting qubit, ion trap, photonic quantum, quantum error correction, quantum gate, quantum supremacy, quantum advantage, NISQ |
| 量子通信 | 量子通信、量子加密、量子密钥分发、量子网络 | quantum communication, quantum cryptography, QKD, quantum key distribution, quantum network |
| 量子精密测量 | 量子精密测量、量子传感、量子雷达、量子陀螺仪 | quantum sensing, quantum sensor, quantum metrology, quantum radar |
| 底层支撑 | 量子算法、量子模拟、量子软件、量子云平台 | quantum algorithm, quantum simulation, quantum software, quantum cloud |
| 产业落地 | 量子药物发现、量子金融、量子化学 | quantum drug discovery, quantum finance, quantum chemistry |

### 3. 数据写入方式：SQL 直接插入

**选择**：通过 sqlite3 命令直接插入 tracks 表和 track_keywords 表。

**理由**：这是纯数据操作，无代码变更。用 SQL 最直接，与现有 5 个赛道的创建方式一致（也是直接插入）。

### 4. color 选择

**选择**：`#13c2c2`（青色/teal）。

**理由**：与现有赛道颜色不冲突（蓝#1890ff、红#ff4d4f、橙#faad14、紫#722ed1、绿#52c41a）。

## Risks / Trade-offs

- **赛道范围较广** → 关键词覆盖量子科技多个子领域，可能命中不属于"量子计算"的资讯。可通过后续微调关键词细化。
- **关键词数量较多（~40个）** → 采集时 OR 匹配，不会对性能造成显著影响。
