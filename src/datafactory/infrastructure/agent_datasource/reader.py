"""直接读取 agent 的 raw JSON 文件目录"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ...domain.models.news import NewsItem

DEFAULT_AGENT_DATA_DIR = Path("/home/ecs-assist-user/d8q-data-agent/data")


class AgentDataReader:
    """读取 data-agent 的文件系统数据（raw JSON + reports + indexes）"""

    def __init__(self, agent_data_dir: Path = DEFAULT_AGENT_DATA_DIR):
        self.data_dir = agent_data_dir
        self.raw_dir = agent_data_dir / "raw"
        self.reports_dir = agent_data_dir / "reports"
        self.indexes_dir = agent_data_dir / "indexes"

    # ---- raw JSON 文件 ----

    def list_sources(self) -> List[str]:
        """列出 raw/ 下所有数据源目录"""
        if not self.raw_dir.exists():
            return []
        return [d.name for d in self.raw_dir.iterdir() if d.is_dir()]

    def list_raw_files(self, source: Optional[str] = None) -> List[Path]:
        """列出 raw JSON 文件，可按 source 过滤"""
        search_dir = (self.raw_dir / source) if source else self.raw_dir
        if not search_dir.exists():
            return []
        return sorted(search_dir.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    def read_raw_file(self, path: Path) -> Dict:
        """读取单个 raw JSON 文件，返回原始 dict"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_raw_items(self, source: Optional[str] = None, limit: int = 200) -> List[NewsItem]:
        """从 raw JSON 文件加载 NewsItem 列表"""
        items: List[NewsItem] = []
        for fp in self.list_raw_files(source):
            if len(items) >= limit:
                break
            try:
                data = self.read_raw_file(fp)
                for entry in data.get("data_items", []):
                    items.append(self._entry_to_item(entry))
                    if len(items) >= limit:
                        break
            except Exception:
                continue
        return items

    # ---- reports ----

    def list_reports(self, report_type: Optional[str] = None) -> List[Path]:
        """列出报告文件，report_type 可选 'quality_report' / 'deduplication_report' / 'storage_report'"""
        search_dir = self.reports_dir
        if not search_dir.exists():
            return []
        files = sorted(search_dir.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if report_type:
            files = [f for f in files if f.name.startswith(report_type)]
        return files

    def read_report(self, path: Path) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---- indexes ----

    def read_platform_index(self) -> Dict:
        idx_file = self.indexes_dir / "financial_news" / "platform_index.json"
        if not idx_file.exists():
            return {}
        with open(idx_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def read_content_hashes(self) -> Dict:
        hash_file = self.indexes_dir / "content_hashes.json"
        if not hash_file.exists():
            return {}
        with open(hash_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---- helpers ----

    @staticmethod
    def _entry_to_item(entry: Dict) -> NewsItem:
        pt = None
        if entry.get("publish_time"):
            try:
                pt = datetime.fromisoformat(entry["publish_time"])
            except ValueError:
                pass
        ca = None
        if entry.get("created_at"):
            try:
                ca = datetime.fromisoformat(entry["created_at"])
            except ValueError:
                pass
        meta = entry.get("metadata", {})
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        return NewsItem(
            item_id=entry.get("id", ""),
            title=entry.get("title", ""),
            content=entry.get("content", ""),
            source=entry.get("source", ""),
            subject=entry.get("subject", ""),
            url=entry.get("url"),
            author=entry.get("author"),
            category=entry.get("category"),
            publish_time=pt,
            created_at=ca,
            metadata=meta,
        )
