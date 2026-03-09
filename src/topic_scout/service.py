from __future__ import annotations

from datetime import datetime

from .analyzer import analyze_sources
from .collector import load_file, load_url
from .llm import LLMEnhancementError, LLMEnhancer
from .models import ResearchRequest, RunRecord, utc_now_iso
from .normalizer import dedupe_items, normalize_platform
from .planner import build_report_plan
from .renderer import render_markdown
from .repository import Repository


class TopicScoutService:
    def __init__(self, repository: Repository, llm_enhancer: LLMEnhancer | None = None) -> None:
        self.repository = repository
        self.llm_enhancer = llm_enhancer

    def ingest_file(self, path: str) -> list:
        items = load_file(path)
        return self._store_items(items)

    def ingest_url(self, url: str):
        item = load_url(url)
        stored = self._store_items([item])
        return stored[0]

    def research(self, request: ResearchRequest) -> RunRecord:
        library = self.repository.load_items()
        items = _filter_items(library, request)
        if not items:
            raise ValueError("No matching source content found. Ingest content first or adjust filters.")
        analysis = analyze_sources(request.topic, items, request)
        report = build_report_plan(request.topic, analysis, request)
        if request.use_llm and self.llm_enhancer is not None:
            try:
                report = self.llm_enhancer.enhance(request.topic, request, items, report)
            except LLMEnhancementError as exc:
                report.generation_mode = "rule-based-fallback"
                report.generation_notes.append(str(exc))
                report.generation_notes.append("Fell back to the deterministic planner output.")
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        markdown = render_markdown(request.topic, report, request, len(items))
        report_path = self.repository.write_report(run_id, markdown)
        record = RunRecord(
            run_id=run_id,
            topic=request.topic,
            created_at=utc_now_iso(),
            report_path=str(report_path),
            request=request.to_dict(),
            report=report.to_dict(),
        )
        self.repository.save_run(record)
        return record

    def get_report(self, run_id: str) -> RunRecord:
        record = self.repository.load_run(run_id)
        if record is None:
            raise FileNotFoundError(f"Unknown run id: {run_id}")
        return record

    def _store_items(self, items):
        merged = dedupe_items(self.repository.load_items() + items)
        self.repository.save_items(merged)
        new_ids = {item.id for item in items}
        return [item for item in merged if item.id in new_ids]


def _filter_items(items, request: ResearchRequest):
    filtered = items
    if request.source_ids:
        allowed = set(request.source_ids)
        filtered = [item for item in filtered if item.id in allowed]
    if request.platforms:
        normalized = {normalize_platform(platform) for platform in request.platforms}
        filtered = [item for item in filtered if item.platform in normalized]
    return filtered
