"""LLM驱动的内容创作引擎 - 资讯速递 + 研究报告"""
import json
import logging
import os
import urllib.request
from datetime import datetime, timedelta

from datafactory.content.llm_config import load_config

logger = logging.getLogger(__name__)

DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"
ARTICLES_DIR = "/home/ecs-assist-user/d8q-intelligentengine-datafactory/articles"
SHARK_API = "http://localhost:5000"

FREQ_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _llm_call(prompt, system="你是专业的内容创作助手。", cfg=None):
    """调用LLM"""
    if cfg is None:
        cfg = load_config()["llm"]
    body = json.dumps({
        "model": cfg["model"],
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "temperature": cfg.get("temperature", 0.7),
        "max_tokens": cfg.get("max_tokens", 2000),
    }).encode()
    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + cfg["api_key"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def _fetch_news(subject, days=1):
    """从数据库获取资讯"""
    import sqlite3
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT title, content, source, publish_time, url FROM financial_news "
        "WHERE subject=? AND publish_time>=? ORDER BY publish_time DESC",
        (subject, cutoff),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _fetch_reports(subject, days=7):
    """从Shark获取研报数据"""
    try:
        url = f"{SHARK_API}/api/report/stock/{subject}?stock_name={subject}&days={days}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning("获取研报失败: %s", e)
        return {"reports": [], "announcements": []}


def _dedup_news(news_list):
    """按标题去重（相似标题只保留第一条）"""
    seen = set()
    result = []
    for n in news_list:
        key = n["title"][:15]  # 前15字相同视为重复
        if key not in seen:
            seen.add(key)
            result.append(n)
    return result


def create_news_brief(subject, freq="daily"):
    """资讯速递 - LLM改写版"""
    cfg = load_config()
    llm_cfg = cfg["llm"]
    style_cfg = cfg["news_brief"]

    days = FREQ_DAYS.get(freq, 1)
    news = _dedup_news(_fetch_news(subject, days))
    if not news:
        return {"error": "无资讯数据", "subject": subject}

    # 构造资讯摘要给LLM
    news_text = "\n".join(
        f"- [{n['title']}] {(n.get('content','')[:150])} (来源:{n.get('source','')}, {(n.get('publish_time',''))[:16]})"
        for n in news[:20]
    )

    # 生成正文
    content_prompt = style_cfg["content_prompt"].replace("{max_items}", str(style_cfg.get("max_items", 5)))
    content_prompt += f"\n\n主题：{subject}\n资讯列表：\n{news_text}"
    body = _llm_call(content_prompt, cfg=llm_cfg)

    # 生成标题
    title_prompt = style_cfg["title_prompt"] + f"\n\n资讯内容摘要：\n{body[:300]}"
    title = _llm_call(title_prompt, cfg=llm_cfg).strip('"').strip("'")[:20]

    # 确保有标签
    if not any(tag in body for tag in style_cfg.get("default_tags", [])):
        body += "\n\n" + " ".join(style_cfg.get("default_tags", []))

    return _save_article(subject, "资讯速递", title, body, len(news), "news_brief")


def create_research_report(subject, freq="weekly"):
    """研究报告 - LLM改写版，结合研报数据"""
    cfg = load_config()
    llm_cfg = cfg["llm"]
    style_cfg = cfg["research_report"]

    days = FREQ_DAYS.get(freq, 7)
    news = _dedup_news(_fetch_news(subject, days))
    reports_data = _fetch_reports(subject, days)
    reports = reports_data.get("reports", [])

    if not news and not reports:
        return {"error": "无数据", "subject": subject}

    # 构造输入
    parts = [f"主题：{subject}\n"]
    if reports:
        parts.append("【研报数据】")
        for r in reports[:15]:
            parts.append(f"- {r.get('title','')} | {r.get('org','')} | {r.get('date','')} | {r.get('summary','')}")
    if news:
        parts.append("\n【行业资讯】")
        for n in news[:10]:
            parts.append(f"- {n['title']} ({n.get('source','')}, {(n.get('publish_time',''))[:10]})")

    input_text = "\n".join(parts)

    # 生成正文
    body = _llm_call(style_cfg["content_prompt"] + "\n\n" + input_text, cfg=llm_cfg)

    # 生成标题
    title = _llm_call(style_cfg["title_prompt"] + f"\n\n内容摘要：\n{body[:300]}", cfg=llm_cfg).strip('"').strip("'")[:20]

    if not any(tag in body for tag in style_cfg.get("default_tags", [])):
        body += "\n\n" + " ".join(style_cfg.get("default_tags", []))

    return _save_article(subject, "研究报告", title, body, len(news) + len(reports), "research_report")


def _save_article(subject, style_name, title, body, data_count, style_key):
    """保存文章到文件"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{style_name}_{subject}.md"
    dir_path = os.path.join(ARTICLES_DIR, subject, date_str)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)

    md = f"# {title}\n\n{body}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md)

    return {
        "path": file_path,
        "relative_path": os.path.relpath(file_path, ARTICLES_DIR),
        "title": title,
        "data_count": data_count,
        "style": style_key,
        "date": date_str,
    }


# 风格映射
STYLE_CREATORS = {
    "news_brief": create_news_brief,
    "research_report": create_research_report,
}
