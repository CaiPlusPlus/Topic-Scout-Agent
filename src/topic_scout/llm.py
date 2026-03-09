from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import ContentItem, ResearchReport, ResearchRequest
from .prompts import SUPPORTED_TEMPLATES, build_system_prompt, build_user_prompt


class LLMConfigurationError(RuntimeError):
    pass


class LLMEnhancementError(RuntimeError):
    pass


class LLMEnhancer:
    def __init__(
        self,
        provider: str,
        api_key: str | None,
        model: str,
        api_base: str,
        timeout: int = 30,
        prompt_template: str = "default-v1",
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.prompt_template = prompt_template

    @classmethod
    def from_env(cls) -> "LLMEnhancer":
        provider = os.getenv("TOPIC_SCOUT_LLM_PROVIDER", "openai-compatible").strip().lower()
        api_key = os.getenv("TOPIC_SCOUT_API_KEY")
        model = os.getenv("TOPIC_SCOUT_MODEL")
        default_api_base = "http://127.0.0.1:11434" if provider == "ollama" else "https://api.openai.com/v1"
        api_base = os.getenv("TOPIC_SCOUT_API_BASE", default_api_base)
        timeout = int(os.getenv("TOPIC_SCOUT_LLM_TIMEOUT", "30"))
        prompt_template = os.getenv("TOPIC_SCOUT_PROMPT_TEMPLATE", "default-v1")
        if provider not in {"openai-compatible", "ollama"}:
            raise LLMConfigurationError("TOPIC_SCOUT_LLM_PROVIDER must be openai-compatible or ollama")
        if prompt_template not in SUPPORTED_TEMPLATES:
            raise LLMConfigurationError(
                f"TOPIC_SCOUT_PROMPT_TEMPLATE must be one of: {', '.join(sorted(SUPPORTED_TEMPLATES))}"
            )
        if provider == "openai-compatible" and (not api_key or not model):
            raise LLMConfigurationError(
                "OpenAI-compatible LLM mode requires TOPIC_SCOUT_API_KEY and TOPIC_SCOUT_MODEL"
            )
        if provider == "ollama" and not model:
            raise LLMConfigurationError("Ollama mode requires TOPIC_SCOUT_MODEL")
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            api_base=api_base,
            timeout=timeout,
            prompt_template=prompt_template,
        )

    def enhance(
        self,
        topic: str,
        request: ResearchRequest,
        items: list[ContentItem],
        draft: ResearchReport,
    ) -> ResearchReport:
        messages = [
            {"role": "system", "content": build_system_prompt(self.prompt_template)},
            {"role": "user", "content": build_user_prompt(self.prompt_template, topic, request, items, draft)},
        ]
        try:
            content = self._request_completion(messages)
            parsed = json.loads(content)
        except urllib.error.URLError as exc:
            raise LLMEnhancementError(f"LLM request failed for provider {self.provider}") from exc
        except json.JSONDecodeError as exc:
            raise LLMEnhancementError("LLM response was not valid JSON") from exc
        report = ResearchReport(
            topic_summary=str(parsed["topic_summary"]),
            trend_clusters=[str(item) for item in parsed["trend_clusters"]],
            competitor_patterns=[str(item) for item in parsed["competitor_patterns"]],
            pain_points=[str(item) for item in parsed["pain_points"]],
            title_angles=[str(item) for item in parsed["title_angles"]],
            outline_suggestions=[str(item) for item in parsed["outline_suggestions"]],
            next_actions=[str(item) for item in parsed["next_actions"]],
            generation_mode=f"llm:{self.provider}",
            generation_notes=[f"Enhanced by provider={self.provider}, template={self.prompt_template}, model={self.model}"],
        )
        return report

    def _request_completion(self, messages: list[dict[str, str]]) -> str:
        if self.provider == "ollama":
            payload = {
                "model": self.model,
                "format": "json",
                "stream": False,
                "messages": messages,
            }
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.api_base}/api/chat",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
            try:
                return raw["message"]["content"]
            except KeyError as exc:
                raise LLMEnhancementError("Ollama response missing message content") from exc

        payload = {
            "model": self.model,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
            "messages": messages,
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
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
        try:
            return raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMEnhancementError("OpenAI-compatible response missing message content") from exc
