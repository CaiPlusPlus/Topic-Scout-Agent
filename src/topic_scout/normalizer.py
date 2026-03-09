from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    "我们",
    "你们",
    "他们",
    "自己",
    "这个",
    "那个",
    "一种",
    "一个",
    "没有",
    "可以",
    "需要",
    "进行",
    "内容",
    "视频",
    "用户",
    "作者",
    "平台",
    "大家",
    "以及",
    "如何",
    "就是",
    "因为",
    "所以",
    "如果",
    "但是",
    "然后",
}


def normalize_platform(value: str | None) -> str:
    if not value:
        return "generic"
    lowered = value.strip().lower()
    aliases = {
        "xhs": "xiaohongshu",
        "xiaohongshu": "xiaohongshu",
        "小红书": "xiaohongshu",
        "douyin": "douyin",
        "抖音": "douyin",
    }
    return aliases.get(lowered, lowered)


def clean_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    compact = re.sub(r"[^\w\u4e00-\u9fff#]+", " ", compact)
    return re.sub(r"\s+", " ", compact).strip()


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}", text)
    counter = Counter(word.lower() for word in words if word not in STOPWORDS)
    return [word for word, _ in counter.most_common(limit)]


def dedupe_items(items: list) -> list:
    seen: set[str] = set()
    deduped = []
    for item in items:
        fingerprint = item.url or item.clean_text[:120] or item.title
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        deduped.append(item)
    return deduped

