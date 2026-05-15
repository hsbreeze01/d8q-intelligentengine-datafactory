# Design: 修复策略订阅无反馈

## 问题定位

`templates/index.html` 中内联 JS 存在两处缺陷：

1. **`api()` 函数（~第 315 行）**：`fetch().then(r => r.json())` 不检查 `r.ok`，HTTP 4xx/5xx 也按正常响应处理
2. **`subscribeStrategy()` / `unsubscribeStrategy()`（~第 469 行）**：`await api(...)` 无 try/catch，API 返回错误时静默失败或显示虚假成功 toast

## 修改方案

### 文件：`templates/index.html`

#### 1. 修改 `api()` 函数

在 `.then(r => r.json())` 之前插入 HTTP status 检查：

```
原：fetch(url, {headers:{'Content-Type':'application/json'},...opt}).then(r=>r.json())
改：fetch(url, {headers:{'Content-Type':'application-json'},...opt}).then(r => {
      if (!r.ok) return r.json().then(d => { throw new Error(d.error || '请求失败 ('+r.status+')') });
      return r.json();
    })
```

- 非 2xx 时先 parse JSON 取 `error` 字段，再 throw Error
- 如果 JSON parse 失败（非 JSON body），浏览器的 `.then()` 链自然抛到后续 catch

#### 2. 修改 `subscribeStrategy()` 函数

包裹 try/catch：

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

#### 3. 修改 `unsubscribeStrategy()` 函数

同理包裹 try/catch，catch 中 `toast(e.message, true)`。

## 影响范围

- 仅修改 `templates/index.html` 中的内联 JavaScript
- `api()` 函数是全局工具函数，增强后影响所有调用方（均为正面影响：错误不再被吞掉）
- 后端无改动
- 无数据库变更
- 无新增依赖

## 测试验证

- `ruff check` 无 Python 变更，不涉及
- `pytest` 现有测试不涉及前端 JS，应全部通过
- 功能验证需人工测试（scope: frontend）
