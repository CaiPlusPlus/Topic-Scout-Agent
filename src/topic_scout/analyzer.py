from __future__ import annotations

from collections import Counter, defaultdict

from .models import ContentItem, ResearchRequest
from .normalizer import extract_keywords


PLATFORM_HINTS = {
    "xiaohongshu": ["清单", "避坑", "对比", "踩雷", "平替", "教程"],
    "douyin": ["反转", "开场", "三秒", "冲突", "演示", "对比"],
    "generic": ["案例", "步骤", "误区", "清单", "经验", "方法"],
}

PAIN_POINT_HINTS = [
    ("不会开始", ["不会", "不知道", "怎么开始", "起号", "入门"]),
    ("缺少差异化", ["同质化", "没流量", "没人看", "没有亮点"]),
    ("效率焦虑", ["来不及", "太慢", "高效", "效率", "省时间"]),
    ("转化压力", ["成交", "转化", "下单", "咨询", "留资"]),
]


def analyze_sources(topic: str, items: list[ContentItem], request: ResearchRequest) -> dict[str, list[str] | str]:
    keyword_counter: Counter[str] = Counter()
    platform_counter: Counter[str] = Counter()
    title_patterns: Counter[str] = Counter()
    snippets_by_keyword: dict[str, list[str]] = defaultdict(list)

    for item in items:
        platform_counter[item.platform] += 1
        keywords = item.tags or extract_keywords(item.clean_text)
        keyword_counter.update(keywords)
        for keyword in keywords[:5]:
            snippets_by_keyword[keyword].append(_short_snippet(item.clean_text, keyword))
        title_patterns.update(_classify_title(item.title))

    dominant_platform = platform_counter.most_common(1)[0][0] if platform_counter else "generic"
    top_keywords = [keyword for keyword, _ in keyword_counter.most_common(8)]

    trend_clusters = []
    for keyword in top_keywords[:4]:
        examples = [snippet for snippet in snippets_by_keyword[keyword] if snippet][:2]
        trend_clusters.append(
            f"{keyword}：高频出现在素材中，常见表达集中在{_format_examples(examples)}。"
        )

    competitor_patterns = []
    for pattern, count in title_patterns.most_common(3):
        competitor_patterns.append(f"{pattern} 型内容出现 {count} 次，适合做结构化借鉴。")
    if not competitor_patterns:
        competitor_patterns.append("样本标题较分散，建议先用“问题 + 结果 + 场景”结构提升点击率。")

    pain_points = _infer_pain_points(items, topic)
    if not pain_points:
        pain_points = [
            f"围绕“{topic}”的内容供给很多，但真正能直接落地的步骤拆解不足。",
            "用户希望少走弯路，更需要模板、案例和结果预期，而不是空泛概念。",
        ]

    topic_summary = (
        f"围绕“{topic}”的样本共 {len(items)} 条，主平台偏向 {dominant_platform}。"
        f" 高频关键词包括：{', '.join(top_keywords[:5]) or topic}。"
        f" 适合优先从 {', '.join(PLATFORM_HINTS.get(dominant_platform, PLATFORM_HINTS['generic'])[:3])} 角度切入。"
    )

    return {
        "topic_summary": topic_summary,
        "trend_clusters": trend_clusters or [f"{topic}：当前样本不足，建议补充更多同主题素材后再聚类。"],
        "competitor_patterns": competitor_patterns,
        "pain_points": pain_points,
        "top_keywords": top_keywords,
        "dominant_platform": dominant_platform,
    }


def _classify_title(title: str) -> list[str]:
    normalized = title.strip()
    patterns = []
    if any(token in normalized for token in ["为什么", "如何", "怎么"]):
        patterns.append("问题解法")
    if any(token in normalized for token in ["清单", "合集", "盘点"]):
        patterns.append("清单盘点")
    if any(token in normalized for token in ["避坑", "别再", "误区"]):
        patterns.append("避坑提醒")
    if any(token in normalized for token in ["对比", "VS", "平替"]):
        patterns.append("对比选择")
    if any(token in normalized for token in ["从0到1", "新手", "入门"]):
        patterns.append("新手入门")
    return patterns or ["经验分享"]


def _short_snippet(text: str, keyword: str) -> str:
    if keyword not in text:
        return text[:24]
    start = max(text.index(keyword) - 8, 0)
    return text[start : start + 24]


def _format_examples(examples: list[str]) -> str:
    if not examples:
        return "「步骤拆解 / 结果承诺」"
    return " / ".join(f"「{example}」" for example in examples)


def _infer_pain_points(items: list[ContentItem], topic: str) -> list[str]:
    corpus = " ".join(item.clean_text for item in items)
    points = []
    for label, hints in PAIN_POINT_HINTS:
        if any(hint in corpus for hint in hints):
            points.append(f"用户在“{topic}”场景里明显存在“{label}”问题，需要更直接的操作框架。")
    return points

