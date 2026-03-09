from __future__ import annotations

import argparse
import json
import sys

from .collector import ContentExtractionError
from .llm import LLMConfigurationError, LLMEnhancementError, LLMEnhancer
from .models import ResearchRequest
from .renderer import render_terminal_summary
from .repository import Repository
from .service import TopicScoutService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="topic-scout", description="Topic research agent for short-form content")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest source content")
    ingest_subparsers = ingest_parser.add_subparsers(dest="ingest_command", required=True)

    ingest_file = ingest_subparsers.add_parser("file", help="Ingest a local file")
    ingest_file.add_argument("path")
    ingest_file.set_defaults(func=cmd_ingest_file)

    ingest_url = ingest_subparsers.add_parser("url", help="Ingest a public URL")
    ingest_url.add_argument("url")
    ingest_url.set_defaults(func=cmd_ingest_url)

    research_parser = subparsers.add_parser("research", help="Generate a research report")
    research_parser.add_argument("topic")
    research_parser.add_argument("--platform", action="append", default=[])
    research_parser.add_argument("--source-id", action="append", default=[])
    research_parser.add_argument("--tone", default="专业但接地气")
    research_parser.add_argument("--audience", default="独立创作者")
    research_parser.add_argument("--llm", action="store_true", help="Enhance the report with an OpenAI-compatible LLM")
    research_parser.set_defaults(func=cmd_research)

    report_parser = subparsers.add_parser("report", help="Show a previous report")
    report_parser.add_argument("run_id")
    report_parser.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repository = Repository()
    try:
        service = _build_service(repository, args)
        return args.func(args, service)
    except (FileNotFoundError, ValueError, ContentExtractionError, LLMConfigurationError, LLMEnhancementError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_ingest_file(args, service: TopicScoutService) -> int:
    items = service.ingest_file(args.path)
    print(f"Ingested {len(items)} item(s)")
    for item in items:
        print(json.dumps(_present_item(item), ensure_ascii=False))
    return 0


def cmd_ingest_url(args, service: TopicScoutService) -> int:
    item = service.ingest_url(args.url)
    print(json.dumps(_present_item(item), ensure_ascii=False))
    return 0


def cmd_research(args, service: TopicScoutService) -> int:
    request = ResearchRequest(
        topic=args.topic,
        platforms=args.platform,
        source_ids=args.source_id,
        tone=args.tone,
        target_audience=args.audience,
        use_llm=args.llm,
    )
    record = service.research(request)
    print(render_terminal_summary(record.run_id, record.report_path, _report_from_record(record)))
    return 0


def cmd_report(args, service: TopicScoutService) -> int:
    record = service.get_report(args.run_id)
    print(f"Run ID: {record.run_id}")
    print(f"Created At: {record.created_at}")
    print(f"Report Path: {record.report_path}")
    print(f"Topic: {record.topic}")
    return 0


def _present_item(item) -> dict[str, str | list[str] | None]:
    return {
        "id": item.id,
        "title": item.title,
        "platform": item.platform,
        "author": item.author,
        "url": item.url,
        "tags": item.tags,
    }


def _report_from_record(record):
    from .models import ResearchReport

    return ResearchReport(**record.report)


def _build_service(repository: Repository, args) -> TopicScoutService:
    llm_enhancer = None
    if getattr(args, "llm", False):
        llm_enhancer = LLMEnhancer.from_env()
    return TopicScoutService(repository, llm_enhancer=llm_enhancer)


if __name__ == "__main__":
    raise SystemExit(main())
