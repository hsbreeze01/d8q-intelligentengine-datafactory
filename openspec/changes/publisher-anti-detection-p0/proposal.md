# Proposal: publisher-anti-detection-p0

## Problem

小红书已检测到非人工访问和发布行为并发出警告。当前自动化发布系统存在三个关键指纹泄漏：

1. **User-Agent 不一致/泄漏**：`ghost-browser/launcher.mjs` 没有配置 `polyfill.userAgent()`，导致 Chromium 使用默认 UA（可能包含 HeadlessChrome 标识）。而登录脚本（login_v2.py）使用 `Chrome/131.0.0.0` UA，登录环境与发布环境 UA 不一致。
2. **screen/viewport 不匹配**：`polyfill.screen({width:1920, height:1080})` 但 `--window-size=1440,900`，screen 对象报告的分辨率与实际 viewport 不同，在服务器环境下非常可疑。
3. **发布时间过于规律**：每天固定 08:30 创作 + 08:40 发布，精确到分钟，行为模式完全不像人类。

## Scope

- **infopublisher** 项目：`ghost-browser/launcher.mjs`（P0-1, P0-2）
- **datafactory** 项目：`app.py` 调度逻辑（P0-3）
- 不涉及其他项目

## Approach

### P0-1: 统一 User-Agent

在 `launcher.mjs` 的 plugins 数组中添加 `polyfill.userAgent()`：

```javascript
plugins: [
    plugins.polyfill.userAgent({
        userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }),
    // ... 其他 plugins 保持不变
]
```

UA 字符串与 login_v2.py 中的保持一致。

### P0-2: 统一 screen 和 window-size

将 `--window-size=1440,900` 改为 `--window-size=1920,1080`，与 `polyfill.screen({width:1920, height:1080})` 保持一致。

同时检查 `login_v2.py` 和 `login_auto.py` 中的 viewport 设置，确保也更新为 1920x1080。

### P0-3: 发布时间随机偏移

修改 datafactory 的 `app.py` 中 scheduler 逻辑：
- 当 `run_at` 为 "08:40" 时，实际执行时间在 08:35 ~ 09:30 之间随机偏移
- 对 creation (08:30) 也加随机偏移：08:25 ~ 09:10
- 偏移量在服务启动时计算一次（不每次不同），确保同一天内 creation 仍然先于 publish

具体实现：在 scheduler 检查 `run_at` 的逻辑中，读取 `run_at` 后加一个 `±random_offset_minutes` 的偏移，偏移范围和方向由每天首次调度时生成的随机种子决定。

## Impact

- 消除 User-Agent 泄漏这一最大的自动化检测向量
- 消除 screen/viewport 不匹配的指纹异常
- 打破固定时间规律，降低行为模式识别风险
- 无功能影响，发布流程不变

## Success Criteria

1. ghost-browser 启动后，通过 CDP 访问页面检查 `navigator.userAgent` 返回 `Chrome/131.0.0.0`（不含 HeadlessChrome）
2. `window.screen.width === 1920 && window.screen.height === 1080` 与 viewport 一致
3. scheduler 触发时间不再是精确的 08:30/08:40，而是在指定范围内随机
4. `systemctl restart d8q-ghost-browser && systemctl restart d8q-infopublisher` 后服务稳定运行
