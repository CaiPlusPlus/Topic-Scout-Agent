from __future__ import annotations

import json

from .models import ContentItem, ResearchReport, ResearchRequest


SUPPORTED_TEMPLATES = {"default-v1", "hook-heavy-v1"}


def build_system_prompt(template_name: str) -> str:
    if template_name == "hook-heavy-v1":
        return (
            "You are a Chinese short-form content strategist. "
            "Return valid JSON only. Make every output concrete, hook-driven, and creator-friendly. "
            "Required keys: topic_summary, trend_clusters, competitor_patterns, pain_points, "
            "title_angles, outline_suggestions, next_actions."
        )
    return (
        "You are a Chinese content strategy assistant. "
        "Return valid JSON only. Keep it concrete, non-generic, and useful for independent creators. "
        "Required keys: topic_summary, trend_clusters, competitor_patterns, pain_points, "
        "title_angles, outline_suggestions, next_actions."
    )


def build_user_prompt(
    template_name: str,
    topic: str,
    request: ResearchRequest,
    items: list[ContentItem],
    draft: ResearchReport,
) -> str:
    style = (
        "Prioritize strong opening hooks, contrast, and repeatable title structures."
        if template_name == "hook-heavy-v1"
        else "Prioritize clear reasoning, practical next steps, and concrete examples."
    )
    sample_items = []
    for item in items[:6]:
        sample_items.append(
            {
                "platform": item.platform,
                "title": item.title,
                "tags": item.tags,
                "snippet": item.clean_text[:180],
            }
        )
    return json.dumps(
        {
            "topic": topic,
            "audience": request.target_audience,
            "tone": request.tone,
            "platforms": request.platforms,
            "draft_report": draft.to_dict(),
            "samples": sample_items,
            "requirements": {
                "language": "zh-CN",
                "title_angles_count": 5,
                "outline_suggestions_count": 3,
                "style": style,
                "template": template_name,
            },
        },
        ensure_ascii=False,
    )
