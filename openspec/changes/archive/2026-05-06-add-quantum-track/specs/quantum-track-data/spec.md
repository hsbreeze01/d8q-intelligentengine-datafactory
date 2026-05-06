## ADDED Requirements

### Requirement: 量子计算赛道记录
系统 SHALL 在 tracks 表中新增"量子计算"赛道，包含名称、颜色、状态和初始关键词列表。

#### Scenario: 赛道记录插入成功
- **WHEN** 执行赛道插入操作
- **THEN** tracks 表新增一行：name="量子计算", color="#13c2c2", status="active", keywords 为包含核心关键词的 JSON 数组

#### Scenario: 赛道可通过 API 查询
- **WHEN** 调用 `GET /api/tracks`
- **THEN** 返回列表包含 id=6 的"量子计算"赛道

### Requirement: 量子计算关键词入库
系统 SHALL 在 track_keywords 表中批量插入覆盖量子科技三大产业、底层支撑和产业落地的中英文关键词。

#### Scenario: 关键词覆盖量子计算核心
- **WHEN** 查看 track_keywords 中 track_name="量子计算" 的记录
- **THEN** 包含：量子计算、量子芯片、量子比特、超导量子、离子阱、光量子、量子纠错、quantum computing, qubit 等

#### Scenario: 关键词覆盖量子通信
- **WHEN** 查看 track_keywords 中 track_name="量子计算" 的记录
- **THEN** 包含：量子通信、量子加密、量子密钥分发、QKD、quantum communication 等

#### Scenario: 关键词覆盖量子精密测量
- **WHEN** 查看 track_keywords 中 track_name="量子计算" 的记录
- **THEN** 包含：量子精密测量、量子传感、quantum sensing, quantum sensor 等

#### Scenario: 关键词覆盖底层支撑与产业落地
- **WHEN** 查看 track_keywords 中 track_name="量子计算" 的记录
- **THEN** 包含：量子算法、量子模拟、量子药物发现、quantum algorithm, quantum chemistry 等

#### Scenario: 关键词总数不少于 35 个
- **WHEN** 统计 track_name="量子计算" 的关键词数量
- **THEN** 总数不少于 35 条（中英文合计）
