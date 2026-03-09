from __future__ import annotations

from .models import ResearchReport, ResearchRequest


def render_markdown(topic: str, report: ResearchReport, request: ResearchRequest, source_count: int) -> str:
    lines = [
        f"# 选题研究报告：{topic}",
        "",
        f"- 目标受众：{request.target_audience}",
        f"- 语气：{request.tone}",
        f"- 平台：{', '.join(request.platforms) if request.platforms else 'auto'}",
        f"- 样本数量：{source_count}",
        "",
        "## 主题概览",
        report.topic_summary,
        "",
        "## 热点聚类",
        *_render_list(report.trend_clusters),
        "",
        "## 竞品套路",
        *_render_list(report.competitor_patterns),
        "",
        "## 受众痛点",
        *_render_list(report.pain_points),
        "",
        "## 标题建议",
        *_render_list(report.title_angles),
        "",
        "## 脚本大纲",
        *_render_list(report.outline_suggestions),
        "",
        "## 下一步行动",
        *_render_list(report.next_actions),
        "",
    ]
    return "\n".join(lines)


def render_terminal_summary(run_id: str, report_path: str, report: ResearchReport) -> str:
    return "\n".join(
        [
            f"Run ID: {run_id}",
            f"Report: {report_path}",
            f"Summary: {report.topic_summary}",
            f"Title Ideas: {len(report.title_angles)}",
            f"Outline Ideas: {len(report.outline_suggestions)}",
        ]
    )


def _render_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]

