## ADDED Requirements

### Requirement: Site validation probe execution
系统 SHALL 提供标准化的站点验证探针脚本，对每个候选材料站点自动执行以下检测：
1. 列表页可访问性和结构解析
2. 详情页字段完整性（标题、正文、日期、作者）
3. 搜索/分类功能可用性
4. 反爬机制强度评估
5. 样本数据采集（至少 5 条）

#### Scenario: Successful validation of a site with HTTP mode
- **WHEN** 对一个静态页面材料站点执行验证探针
- **THEN** 系统输出 JSON 验证报告，包含 list_page、detail_page、anti_crawl、search、sample_data 字段，status 为 "pass" 或 "fail" 或 "partial"

#### Scenario: Validation detects strong anti-crawl protection
- **WHEN** 站点返回验证码、频率限制或浏览器指纹检测
- **THEN** 探针在 anti_crawl 字段记录 level 为 "high"，并在 notes 中描述具体机制，status 为 "fail" 或 "partial"

#### Scenario: Validation with Playwright mode fallback
- **WHEN** HTTP 模式无法获取完整页面内容（JavaScript 动态渲染）
- **THEN** 探针自动切换到 Playwright 模式重新验证，并在报告中标注 mode 为 "playwright"

### Requirement: Standardized validation report format
每个站点的验证结果 SHALL 以统一 JSON 格式输出，包含 site、status、mode、list_page、detail_page、anti_crawl、search、sample_data、recommendation 字段。

#### Scenario: Validation report contains all required fields
- **WHEN** 验证探针完成执行
- **THEN** 输出 JSON 包含所有必填字段：site（站点域名）、status（pass/fail/partial）、mode（http/playwright）、list_page.accessible、detail_page.title、anti_crawl.level、sample_data（数组）

### Requirement: Pass/fail validation criteria
系统 SHALL 定义明确的通过/失败标准：
- **通过 (pass)**：列表页可访问，详情页至少有标题+日期+正文，反爬 level ≤ low，样本数据 ≥ 3 条
- **部分通过 (partial)**：满足部分条件但有关键字段缺失或中等反爬
- **失败 (fail)**：列表页不可访问，或反爬 level = high，或样本数据 = 0

#### Scenario: Site passes validation
- **WHEN** 站点验证结果为：list_page.accessible=true，detail_page 有 title+date+content，anti_crawl.level="none"，sample_data 有 5 条
- **THEN** status 判定为 "pass"，recommendation 建议纳入可用资讯源

#### Scenario: Site fails validation
- **WHEN** 站点返回 403/503，或需要登录才能查看内容
- **THEN** status 判定为 "fail"，recommendation 建议排除或标记为需浏览器模式

### Requirement: Candidate site list management
系统 SHALL 维护候选验证站点列表，包含国内和国际站点，每个站点标注优先级（high/medium/low）和预期技术模式。

#### Scenario: List all candidate sites
- **WHEN** 查看候选站点列表
- **THEN** 系统返回站点清单，包含站点名称、URL、优先级、预期模式（http/playwright）、赛道关联（新材料/碳纤维/通用）
