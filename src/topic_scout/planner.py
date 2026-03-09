from __future__ import annotations

from .models import ResearchReport, ResearchRequest


def build_report_plan(topic: str, analysis: dict, request: ResearchRequest) -> ResearchReport:
    keywords = analysis.get("top_keywords", []) or [topic]
    platform = analysis.get("dominant_platform", "generic")
    title_angles = _build_titles(topic, keywords, platform, request.target_audience)
    outlines = _build_outlines(topic, keywords, request.target_audience)
    next_actions = [
        "挑选 1 个标题方向先做小样，验证评论区反馈和完播表现。",
        "从现有素材里补 3 个真实案例，增强说服力和可复制性。",
        f"针对 {request.target_audience} 再拆一版更窄的场景表达，提升点击和收藏意图。",
    ]
    return ResearchReport(
        topic_summary=str(analysis["topic_summary"]),
        trend_clusters=list(analysis["trend_clusters"]),
        competitor_patterns=list(analysis["competitor_patterns"]),
        pain_points=list(analysis["pain_points"]),
        title_angles=title_angles,
        outline_suggestions=outlines,
        next_actions=next_actions,
    )


def _build_titles(topic: str, keywords: list[str], platform: str, audience: str) -> list[str]:
    hooks = keywords[:3] if keywords else [topic]
    templates = [
        f"做 {topic} 总是没结果？用这套 {hooks[0]} 框架，{audience} 也能快速起步",
        f"{topic} 别再凭感觉做了：3 个高频套路 + 1 个更容易出圈的切口",
        f"我研究了最近的 {topic} 内容，发现最容易被忽略的是「{hooks[-1]}」",
        f"{platform} 上关于 {topic} 的爆款，大多都在重复这 3 个表达方式",
        f"新手做 {topic}，先别卷数量，先把这份实用清单讲明白",
    ]
    return templates[:5]


def _build_outlines(topic: str, keywords: list[str], audience: str) -> list[str]:
    primary = keywords[0] if keywords else topic
    secondary = keywords[1] if len(keywords) > 1 else "结果"
    tertiary = keywords[2] if len(keywords) > 2 else "案例"
    return [
        f"开场痛点：点出 {audience} 在 {topic} 上最常见的卡点；主体：用 {primary} 拆 3 步；结尾：给出立刻可执行的检查表。",
        f"开场对比：先讲做错 {topic} 的常见后果；主体：对比普通做法和围绕 {secondary} 的优化做法；结尾：引导收藏复用。",
        f"开场结论：直接抛出关于 {topic} 的反常识观点；主体：用 {tertiary} 案例解释原因；结尾：补一条避坑提醒。",
    ]

