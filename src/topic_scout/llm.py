from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import ContentItem, ResearchReport, ResearchRequest


class LLMConfigurationError(RuntimeError):
    pass


class LLMEnhancementError(RuntimeError):
    pass


class LLMEnhancer:
    def __init__(self, api_key: str, model: str, api_base: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "LLMEnhancer":
        api_key = os.getenv("TOPIC_SCOUT_API_KEY")
        model = os.getenv("TOPIC_SCOUT_MODEL")
        api_base = os.getenv("TOPIC_SCOUT_API_BASE", "https://api.openai.com/v1")
        timeout = int(os.getenv("TOPIC_SCOUT_LLM_TIMEOUT", "30"))
        if not api_key or not model:
            raise LLMConfigurationError("LLM mode requires TOPIC_SCOUT_API_KEY and TOPIC_SCOUT_MODEL")
        return cls(api_key=api_key, model=model, api_base=api_base, timeout=timeout)

    def enhance(
        self,
        topic: str,
        request: ResearchRequest,
        items: list[ContentItem],
        draft: ResearchReport,
    ) -> ResearchReport:
        payload = {
            "model": self.model,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Chinese content strategy assistant. "
                        "Return valid JSON with keys: topic_summary, trend_clusters, competitor_patterns, "
                        "pain_points, title_angles, outline_suggestions, next_actions."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_prompt(topic, request, items, draft),
                },
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LLMEnhancementError("LLM request failed") from exc
        try:
            content = raw["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMEnhancementError("LLM response was not valid JSON") from exc
        return ResearchReport(
            topic_summary=str(parsed["topic_summary"]),
            trend_clusters=[str(item) for item in parsed["trend_clusters"]],
            competitor_patterns=[str(item) for item in parsed["competitor_patterns"]],
            pain_points=[str(item) for item in parsed["pain_points"]],
            title_angles=[str(item) for item in parsed["title_angles"]],
            outline_suggestions=[str(item) for item in parsed["outline_suggestions"]],
            next_actions=[str(item) for item in parsed["next_actions"]],
        )

    def _build_prompt(
        self,
        topic: str,
        request: ResearchRequest,
        items: list[ContentItem],
        draft: ResearchReport,
    ) -> str:
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
                    "style": "concrete, non-generic, useful for independent creators",
                },
            },
            ensure_ascii=False,
        )
