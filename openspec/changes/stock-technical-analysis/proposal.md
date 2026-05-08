# Proposal: 个股详情页技术分析Tab：替换当前switchSDTab('tech')中的占位符，实现完整的技术分析面板。包括：(1)MA/MACD/KDJ/BOLL/RSI指标图表切换（用echarts，已有CDN），(2)技术信号汇总面板（每个指标显示名称/数值/信号判定），(3)综合判定文字。只修改index.html中switchSDTab函数的tech case分支，不需要新增后端API。参考现有loadSDQuote函数中的drawKline/drawMockKline模式。

## Summary
个股详情页技术分析Tab：替换当前switchSDTab('tech')中的占位符，实现完整的技术分析面板。包括：(1)MA/MACD/KDJ/BOLL/RSI指标图表切换（用echarts，已有CDN），(2)技术信号汇总面板（每个指标显示名称/数值/信号判定），(3)综合判定文字。只修改index.html中switchSDTab函数的tech case分支，不需要新增后端API。参考现有loadSDQuote函数中的drawKline/drawMockKline模式。

## Motivation

## Expected Behavior

