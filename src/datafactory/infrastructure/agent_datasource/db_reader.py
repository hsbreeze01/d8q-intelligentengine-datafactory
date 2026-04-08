"""直接读取 agent 的 SQLite 数据库"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...domain.models.news import NewsItem

# agent 数据目录的默认位置（同一台机器）
DEFAULT_AGENT_DATA_DIR = Path("/home/ecs-assist-user/d8q-data-agent/data")


class AgentDBReader:
    """读取 data-agent 的 financial_news.db 和 task_store.db"""

    def __init__(self, agent_data_dir: Path = DEFAULT_AGENT_DATA_DIR):
        self.news_db = agent_data_dir / "financial_news.db"
        self.task_db = agent_data_dir / "task_store.db"

    # ---- financial_news ----

    def _row_to_item(self, row: sqlite3.Row) -> NewsItem:
        meta = {}
        if row["metadata"]:
            try:
                meta = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        pt = None
        if row["publish_time"]:
            try:
                pt = datetime.fromisoformat(row["publish_time"])
            except ValueError:
                pass
        ca = None
        if row["created_at"]:
            try:
                ca = datetime.fromisoformat(row["created_at"])
            except ValueError:
                pass
        return NewsItem(
            item_id=row["item_id"],
            title=row["title"],
            content=row["content"],
            source=row["source"],
            subject=row["subject"],
            url=row["url"],
            author=row["author"],
            category=row["category"],
            publish_time=pt,
            created_at=ca,
            metadata=meta,
        )

    def _query_news(self, sql: str, params: tuple = ()) -> List[NewsItem]:
        conn = sqlite3.connect(self.news_db)
        conn.row_factory = sqlite3.Row
        try:
            return [self._row_to_item(r) for r in conn.execute(sql, params)]
        finally:
            conn.close()

    def get_all_news(self, limit: int = 100) -> List[NewsItem]:
        return self._query_news(
            "SELECT * FROM financial_news ORDER BY created_at DESC LIMIT ?", (limit,)
        )

    def get_news_by_source(self, source: str, limit: int = 100) -> List[NewsItem]:
        return self._query_news(
            "SELECT * FROM financial_news WHERE source=? ORDER BY created_at DESC LIMIT ?",
            (source, limit),
        )

    def get_news_by_subject(self, subject: str, limit: int = 100) -> List[NewsItem]:
        return self._query_news(
            "SELECT * FROM financial_news WHERE subject=? ORDER BY created_at DESC LIMIT ?",
            (subject, limit),
        )

    def get_news_since(self, since: datetime, limit: int = 500) -> List[NewsItem]:
        return self._query_news(
            "SELECT * FROM financial_news WHERE created_at>=? ORDER BY created_at DESC LIMIT ?",
            (since.isoformat(), limit),
        )

    def count_news(self) -> int:
        conn = sqlite3.connect(self.news_db)
        try:
            return conn.execute("SELECT count(*) FROM financial_news").fetchone()[0]
        finally:
            conn.close()

    # ---- task_store (调度信息) ----

    def list_scheduled_tasks(self) -> list:
        conn = sqlite3.connect(self.task_db)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM scheduled_tasks")]
        finally:
            conn.close()

    def get_recent_executions(self, limit: int = 20) -> list:
        conn = sqlite3.connect(self.task_db)
        conn.row_factory = sqlite3.Row
        try:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM task_executions ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                )
            ]
        finally:
            conn.close()
