"""Factory 领域模型 — 资讯条目"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class NewsItem:
    """从 agent 采集数据映射而来的资讯条目"""
    item_id: str
    title: str
    content: str
    source: str                          # cailianshe / nbd / 36kr / weibo
    subject: str                         # 采集主题，如 "AI" "具身智能"
    url: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    publish_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
