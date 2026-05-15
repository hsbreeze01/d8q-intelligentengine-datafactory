# Proposal: 修复策略订阅无反馈问题

## Summary
策略发现页点击"订阅"按钮后无任何反馈（不成功、不报错、无 toast）。

## Motivation
用户点击订阅后完全无反应，功能不可用。需要修复两个层面：
1. **前端错误处理缺失**：`api()` 和 `subscribeStrategy()` 没有处理 API 错误响应
2. **订阅 API 可能返回 401**：未登录用户点击订阅时，应提示"请先登录"而非静默失败

## Root Cause Analysis

### 前端问题
1. `api()` 函数（第 315 行）是 `fetch(url, opt).then(r => r.json())` — **没有检查 `r.ok`**，无论 HTTP 状态码如何都尝试 parse JSON
2. `subscribeStrategy(gid)` 函数（第 469 行）`await api(...)` 没有 try/catch — 如果 API 返回错误对象，代码继续执行到 `toast('已订阅')` 显示虚假成功
3. 如果 JSON parse 失败（非 JSON 响应），await 抛异常但无人 catch → 静默失败

### 后端认证
- Factory 代理 `/api/strategy/subscribe` 时从 `session.get("username")` 取用户名
- 如果用户未登录，`username` 为空字符串 → Compass `_require_login()` 返回 None → 401
- 前端不处理 401，静默失败

## Expected Behavior
1. 已登录用户点击订阅 → 成功订阅 → toast "已订阅" → 刷新列表
2. 未登录用户点击订阅 → toast "请先登录" → 不执行订阅
3. API 返回其他错误 → toast 显示具体错误信息

## Scope
- **DataFactory**: `templates/index.html` — 修复 `api()` 函数增加错误处理 + 修复 `subscribeStrategy()`/`unsubscribeStrategy()` 增加错误反馈

## Target Projects
- d8q-intelligentengine-datafactory

## 修复方案

### 1. 增强 `api()` 函数（第 315 行）
改为检查 HTTP status，非 2xx 时抛出包含错误信息的异常：
```javascript
function api(url, opt) {
  return fetch(url, {headers: {'Content-Type': 'application/json'}, ...opt})
    .then(r => {
      if (!r.ok) return r.json().then(d => { throw new Error(d.error || '请求失败 (' + r.status + ')') });
      return r.json();
    });
}
```

### 2. 修复 `subscribeStrategy()` / `unsubscribeStrategy()` 加 try/catch
```javascript
async function subscribeStrategy(gid) {
  try {
    await api('/api/strategy/subscribe', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({strategy_group_id:gid})});
    toast('已订阅');
    loadStrategyDiscover(document.getElementById('contentArea'));
  } catch(e) {
    toast(e.message, true);
  }
}
```

同理 `unsubscribeStrategy()` 也要加 try/catch。
