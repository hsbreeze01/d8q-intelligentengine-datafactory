## Why

平台现有 5 个赛道（人工智能、具身智能、新材料、合成生物、碳纤维），缺少量子科技方向的覆盖。用户反馈指出量子科技覆盖三大产业（量子计算、量子通信、量子精密测量）及底层支撑与产业落地，需要新增"量子计算"赛道及其关键词体系。

## What Changes

- 在 `financial_news.db` 的 `tracks` 表中新增"量子计算"赛道记录（id=6, color=#13c2c2）
- 在 `task_store.db` 的 `track_keywords` 表中批量插入关键词，覆盖：
  - 核心产业：量子计算、量子通信、量子精密测量
  - 底层技术：量子芯片、量子比特、超导量子、离子阱、光量子、量子纠错、量子退相干
  - 应用与产业：量子加密、量子密钥分发（QKD）、量子传感、量子模拟、量子药物发现、量子金融
  - 英文检索词：quantum computing, quantum communication, qubit, quantum key distribution, quantum sensor, quantum annealing, quantum supremacy, NISQ

## Capabilities

### New Capabilities
- `quantum-track-data`: 新增量子计算赛道及其关键词数据入库

### Modified Capabilities
（无，不涉及现有功能变更）

## Impact

- **数据库**: `financial_news.db` tracks 表新增 1 行；`task_store.db` track_keywords 表新增约 30+ 行
- **前端**: 赛道页、采集任务表单的赛道下拉框自动展示新赛道（数据驱动，无需前端代码变更）
- **后端**: 无代码变更，数据驱动
