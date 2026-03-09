from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from topic_scout.llm import LLMEnhancementError
from topic_scout.repository import Repository
from topic_scout.service import TopicScoutService
from topic_scout.web import TopicScoutWebApp


ROOT = Path(__file__).resolve().parents[1]


class WebTestCase(unittest.TestCase):
    def test_home_renders_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = TopicScoutWebApp(Repository(tmpdir))
            page = app.render_home()
            self.assertIn("Minimal Web UI", page)
            self.assertIn("还没有素材", page)

    def test_research_action_returns_report_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = TopicScoutWebApp(Repository(root))
            app.service.ingest_file(str(ROOT / "tests" / "fixtures" / "sample_note.txt"))
            flash = app.handle_research(
                {
                    "topic": ["AI 效率"],
                    "audience": ["独立创作者"],
                    "tone": ["专业但接地气"],
                    "platforms": [""],
                }
            )
            self.assertIn("/report/", flash)

    def test_web_app_shows_fallback_note_after_llm_failure(self) -> None:
        class BrokenEnhancer:
            def enhance(self, topic, request, items, draft):
                raise LLMEnhancementError("network down")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = TopicScoutWebApp(Repository(root), llm_enhancer=BrokenEnhancer())
            app.service.ingest_file(str(ROOT / "tests" / "fixtures" / "sample_note.txt"))
            flash = app.handle_research(
                {
                    "topic": ["AI 效率"],
                    "audience": ["独立创作者"],
                    "tone": ["专业但接地气"],
                    "platforms": [""],
                    "use_llm": ["1"],
                }
            )
            run_id = flash.split("/report/")[1].split('"')[0]
            report_page = app.render_report(run_id)
            self.assertIn("rule-based-fallback", report_page)
            self.assertIn("network down", report_page)
