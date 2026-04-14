"""内容创作引擎 - 基于资讯数据生成不同风格的文章"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"
ARTICLES_DIR = "/home/ecs-assist-user/d8q-intelligentengine-datafactory/articles"

# 频率对应的时间范围（天）
FREQ_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def fetch_news(subject, days=1):
    """从数据库获取指定主题和时间范围的资讯"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT title, content, source, author, publish_time, url "
        "FROM financial_news WHERE subject=? AND publish_time>=? "
        "ORDER BY publish_time DESC",
        (subject, cutoff),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render_news_brief(subject, news_list, date_str):
    """资讯速递风格 - 简洁列表"""
    lines = [
        "# %s 资讯速递" % subject,
        "",
        "> %s | 共 %d 条资讯" % (date_str, len(news_list)),
        "",
    ]
    for i, n in enumerate(news_list, 1):
        src = n.get("source", "")
        t = (n.get("publish_time") or "")[:16]
        lines.append("## %d. %s" % (i, n["title"]))
        lines.append("")
        content = n.get("content", "")
        if len(content) > 200:
            content = content[:200] + "..."
        lines.append(content)
        lines.append("")
        lines.append("*来源: %s | %s*" % (src, t))
        lines.append("")
    lines.append("---")
    lines.append("*由 D8Q 智能资讯工厂自动生成*")
    return "\n".join(lines)


def render_deep_analysis(subject, news_list, date_str):
    """深度分析风格 - 带趋势总结"""
    sources = {}
    for n in news_list:
        s = n.get("source", "未知")
        sources[s] = sources.get(s, 0) + 1

    lines = [
        "# %s 深度分析" % subject,
        "",
        "> 分析周期: %s | 数据来源: %d 条资讯" % (date_str, len(news_list)),
        "",
        "## 概览",
        "",
        "本期共收录 %d 条 %s 相关资讯，" % (len(news_list), subject),
        "覆盖 %s 等数据源。" % "、".join(sources.keys()),
        "",
        "## 核心要闻",
        "",
    ]
    for i, n in enumerate(news_list[:10], 1):
        lines.append("### %d. %s" % (i, n["title"]))
        lines.append("")
        content = n.get("content", "")
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(content)
        lines.append("")
        lines.append("*%s | %s*" % (n.get("source", ""), (n.get("publish_time") or "")[:16]))
        lines.append("")

    if len(news_list) > 10:
        lines.append("## 其他资讯")
        lines.append("")
        for n in news_list[10:]:
            lines.append("- **%s** (%s)" % (n["title"], n.get("source", "")))
        lines.append("")

    lines.append("---")
    lines.append("*由 D8Q 智能资讯工厂自动生成*")
    return "\n".join(lines)


def render_investment_weekly(subject, news_list, date_str):
    """投资周报风格 - 数据+趋势"""
    by_date = {}
    for n in news_list:
        d = (n.get("publish_time") or "")[:10]
        by_date.setdefault(d, []).append(n)

    lines = [
        "# %s 投资周报" % subject,
        "",
        "> %s | 共 %d 条资讯 | 覆盖 %d 天" % (date_str, len(news_list), len(by_date)),
        "",
        "## 本期数据概览",
        "",
        "| 日期 | 资讯数量 |",
        "|------|----------|",
    ]
    for d in sorted(by_date.keys(), reverse=True):
        lines.append("| %s | %d |" % (d, len(by_date[d])))
    lines.append("")
    lines.append("## 重点资讯")
    lines.append("")
    for i, n in enumerate(news_list[:15], 1):
        lines.append("%d. **%s** - %s (%s)" % (
            i, n["title"], n.get("source", ""), (n.get("publish_time") or "")[:10]))
    lines.append("")
    lines.append("---")
    lines.append("*由 D8Q 智能资讯工厂自动生成*")
    return "\n".join(lines)


STYLE_RENDERERS = {
    "news_brief": render_news_brief,
    "deep_analysis": render_deep_analysis,
    "investment_weekly": render_investment_weekly,
}


def create_article(subject, style="news_brief", freq="daily"):
    """创建文章并保存到目录

    Returns: {"path", "title", "news_count", "style"}
    """
    days = FREQ_DAYS.get(freq, 1)
    news_list = fetch_news(subject, days=days)

    if not news_list:
        return {"error": "无资讯数据", "subject": subject, "days": days}

    date_str = datetime.now().strftime("%Y-%m-%d")
    renderer = STYLE_RENDERERS.get(style, render_news_brief)
    content = renderer(subject, news_list, date_str)

    # 生成文件路径: articles/{主题}/{日期}/{日期}_{title}.md
    style_names = {"news_brief": "资讯速递", "deep_analysis": "深度分析", "investment_weekly": "投资周报"}
    title = "%s_%s" % (style_names.get(style, style), subject)
    safe_title = title.replace("/", "_").replace(" ", "_")
    filename = "%s_%s.md" % (date_str, safe_title)

    dir_path = os.path.join(ARTICLES_DIR, subject, date_str)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "path": file_path,
        "relative_path": os.path.relpath(file_path, ARTICLES_DIR),
        "title": title,
        "news_count": len(news_list),
        "style": style,
        "date": date_str,
    }
