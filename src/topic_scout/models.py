from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ContentItem:
    id: str
    source_type: str
    platform: str
    url: str | None
    title: str
    author: str | None
    published_at: str | None
    tags: list[str] = field(default_factory=list)
    raw_text: str = ""
    clean_text: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContentItem":
        return cls(**payload)


@dataclass
class ResearchRequest:
    topic: str
    platforms: list[str]
    source_ids: list[str]
    tone: str = "专业但接地气"
    target_audience: str = "独立创作者"
    use_llm: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchReport:
    topic_summary: str
    trend_clusters: list[str]
    competitor_patterns: list[str]
    pain_points: list[str]
    title_angles: list[str]
    outline_suggestions: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunRecord:
    run_id: str
    topic: str
    created_at: str
    report_path: str
    request: dict[str, Any]
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunRecord":
        return cls(**payload)
