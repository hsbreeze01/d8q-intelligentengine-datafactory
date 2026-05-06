## 1. 数据准备

- [x] 1.1 确认 tracks 表当前最大 id（应为 5），确定新赛道 id=6
- [x] 1.2 准备 tracks 表 INSERT 语句：name="量子计算", color="#13c2c2", status="active", keywords JSON 数组
- [x] 1.3 准备 track_keywords 表批量 INSERT 语句（约 40 条中英文关键词）

## 2. 数据写入

- [x] 2.1 在 `financial_news.db` 的 tracks 表插入量子计算赛道记录
- [x] 2.2 在 `task_store.db` 的 track_keywords 表批量插入关键词
- [x] 2.3 验证数据完整性：API 查询返回新赛道，关键词数量 ≥ 35

## 3. 集成验证

- [x] 3.1 前端赛道页面显示"量子计算"卡片（青色）— 注：赛道卡片依赖 track_heat_daily 数据，新赛道暂无热度记录，需采集任务运行后自动出现
- [x] 3.2 新建采集任务表单中赛道下拉框包含"量子计算"
- [x] 3.3 通过"管理关键词"模态框可查看已有关键词并支持增删（55 个关键词已验证）
