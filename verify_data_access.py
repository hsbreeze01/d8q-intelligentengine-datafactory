"""验证 factory 对 agent 数据的访问能力"""

import sys
sys.path.insert(0, "src")

from datafactory.infrastructure.agent_datasource import AgentDataReader, AgentDBReader


def main():
    print("=" * 60)
    print("DataFactory → Agent 数据对接验证")
    print("=" * 60)

    # 1. 数据库读取
    print("\n📦 [DB] financial_news.db")
    db = AgentDBReader()
    count = db.count_news()
    print(f"  总记录数: {count}")
    news = db.get_all_news(limit=3)
    for n in news:
        print(f"  - [{n.source}] {n.title[:40]}... ({n.publish_time})")

    # 2. 调度任务
    print("\n⏰ [DB] 调度任务")
    tasks = db.list_scheduled_tasks()
    for t in tasks:
        print(f"  - {t['id']}: {t['subject']} | cron={t['cron_expr']} | enabled={t['enabled']}")

    execs = db.get_recent_executions(limit=5)
    print(f"  最近执行记录: {len(execs)} 条")
    for e in execs:
        print(f"    {e['started_at']} | {e['status']} | count={e['result_count']}")

    # 3. 文件系统读取
    print("\n📂 [File] raw 数据源")
    reader = AgentDataReader()
    sources = reader.list_sources()
    print(f"  数据源目录: {sources}")

    for src in sources:
        files = reader.list_raw_files(src)
        print(f"  {src}: {len(files)} 个 JSON 文件")

    # 4. 加载 raw items
    print("\n📰 [File] raw 数据条目")
    items = reader.load_raw_items(limit=5)
    print(f"  加载了 {len(items)} 条")
    for item in items:
        print(f"  - [{item.source}/{item.subject}] {item.title[:40]}...")

    # 5. 报告
    print("\n📊 [File] 报告文件")
    reports = reader.list_reports()
    print(f"  报告总数: {len(reports)}")
    for r in reports[:3]:
        print(f"  - {r.name}")

    # 6. 索引
    print("\n🔗 [File] 索引")
    idx = reader.read_platform_index()
    for platform, files in idx.items():
        print(f"  {platform}: {len(files)} 个文件索引")

    hashes = reader.read_content_hashes()
    print(f"  内容哈希: {len(hashes)} 条")

    print("\n" + "=" * 60)
    print("✅ 数据对接验证完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
