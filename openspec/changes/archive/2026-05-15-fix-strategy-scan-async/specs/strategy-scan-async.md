# Delta Spec: 策略扫描异步化

## MODIFIED Requirements

### REQ-ASYNC-001: 扫描触发接口改为异步响应

`POST /api/strategy/{group_id}/scan` 接口 SHALL 在收到请求后立即返回 HTTP 202，响应体包含 `run_id` 和 `status: "running"`。扫描的实际执行 SHALL 在后台线程中进行，不阻塞 HTTP worker。

#### Scenario: 手动触发扫描立即返回

```gherkin
Given 策略组 {group_id} 存在且可扫描
When 用户发送 POST /api/strategy/{group_id}/scan
Then 响应状态码为 202
And 响应体包含 run_id（正整数）和 status="running"
And 响应在 3 秒内返回
```

#### Scenario: 扫描期间其他 API 正常可用

```gherkin
Given 一个策略扫描正在后台执行
When 用户发送 GET /api/strategy/groups
Then 响应状态码为 200
And 返回正常的策略组列表数据
```

#### Scenario: 扫描失败时记录错误状态

```gherkin
Given 后台扫描过程中发生异常
When 扫描线程捕获到异常
Then strategy_group_run 表中对应 run_id 的 status SHALL 更新为 "failed"
And error_message 字段 SHALL 记录异常信息
```

### REQ-ASYNC-002: 扫描后台执行模型

扫描 SHALL 在独立的后台 daemon 线程中执行 scanner.scan() 和 aggregator.aggregate()。主线程仅负责创建 run 记录并启动后台线程。

#### Scenario: 后台线程完成扫描

```gherkin
Given 后台扫描线程已启动，run_id 已创建
When scanner.scan() 和 aggregator.aggregate() 执行完成
Then strategy_group_run 表中对应 run_id 的 status SHALL 更新为 "completed"
And signals_count、events_count 等统计字段 SHALL 被填充
```

### REQ-ASYNC-003: LLM 分析与扫描聚合流程解耦

LLM 分析 SHALL 从聚合器主流程中完全剥离。聚合器在创建 group_event 后 SHALL 以 fire-and-forget 方式启动独立线程执行 LLM 分析。聚合器 SHALL 不等待 LLM 分析结果，不因 LLM 分析失败而影响聚合结果。

#### Scenario: 聚合完成时 LLM 分析尚未完成

```gherkin
Given 聚合器为某事件创建了 group_event 记录
When 聚合器以 fire-and-forget 启动 LLM 分析线程
Then 聚合器 SHALL 立即继续处理下一个事件
And 聚合总耗时 SHALL 不包含任何 LLM 调用等待时间
```

#### Scenario: LLM 分析成功完成

```gherkin
Given 聚合器已为 event_id 创建了 group_event
When LLM 分析后台线程成功完成
Then group_event 的 llm_analysis 字段 SHALL 被更新为分析结果
And llm_analyzed_at 时间戳 SHALL 被记录
```

#### Scenario: LLM 分析失败不影响事件记录

```gherkin
Given LLM 分析后台线程启动
When LLM 分析过程抛出异常（超时/API 错误）
Then 异常 SHALL 被捕获并记录 warning 日志
And group_event 记录 SHALL 保持不变（已有聚合数据完整）
And 扫描 run 的 status 不受影响
```

## ADDED Requirements

### REQ-ASYNC-004: Scanner 支持 run_id 复用和 LLM 跳过

Scanner.scan() 方法 SHALL 接受 `run_id` 参数用于复用已创建的 run 记录，以及 `skip_llm` 参数用于跳过 LLM 分析调用。

#### Scenario: 使用预创建的 run_id 执行扫描

```gherkin
Given 路由层已创建 run 记录（run_id=42）
When Scanner.scan(group_id, run_id=42, skip_llm=True) 被调用
Then Scanner SHALL 使用 run_id=42 记录扫描结果
And SHALL 不创建新的 run 记录
```

### REQ-ASYNC-005: Factory 代理层扫描请求 timeout 调整

DataFactory 的策略代理路由对扫描请求 SHALL 设置合理的 timeout，确保代理仅等待 run 记录创建（<=10s），不等待扫描完成。

#### Scenario: 代理转发扫描请求

```gherkin
Given DataFactory 收到 POST /api/strategy/{group_id}/scan 请求
When 代理将请求转发到 Compass 服务
Then 代理 SHALL 使用不超过 10s 的 timeout
And 如果 Compass 返回 202，代理 SHALL 将 202 状态码和响应体原样返回
```

#### Scenario: 代理超时容错

```gherkin
Given Compass 服务响应延迟超过 proxy timeout
When 代理请求超时
Then 代理 SHALL 返回 502 和明确的错误信息
And 错误信息 SHALL 包含 "timeout" 关键词
```
