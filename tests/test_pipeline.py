from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from topic_scout.collector import ContentExtractionError, load_file
from topic_scout.models import ResearchRequest
from topic_scout.repository import Repository
from topic_scout.service import TopicScoutService


ROOT = Path(__file__).resolve().parents[1]


class PipelineTestCase(unittest.TestCase):
    def test_load_multiple_file_formats(self) -> None:
        txt_items = load_file(str(ROOT / "tests" / "fixtures" / "sample_note.txt"))
        csv_items = load_file(str(ROOT / "tests" / "fixtures" / "sample_posts.csv"))
        json_items = load_file(str(ROOT / "tests" / "fixtures" / "sample_posts.json"))
        self.assertEqual(len(txt_items), 1)
        self.assertEqual(len(csv_items), 2)
        self.assertEqual(len(json_items), 1)
        self.assertEqual(json_items[0].platform, "xiaohongshu")

    def test_empty_research_requires_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = TopicScoutService(Repository(tmpdir))
            with self.assertRaisesRegex(ValueError, "Ingest content first"):
                service.research(ResearchRequest(topic="效率", platforms=[], source_ids=[]))

    def test_research_generates_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            service = TopicScoutService(Repository(root))
            service.ingest_file(str(ROOT / "tests" / "fixtures" / "sample_note.txt"))
            service.ingest_file(str(ROOT / "tests" / "fixtures" / "sample_posts.csv"))
            record = service.research(
                ResearchRequest(
                    topic="效率选题",
                    platforms=[],
                    source_ids=[],
                    target_audience="独立创作者",
                )
            )
            report_path = Path(record.report_path)
            self.assertTrue(report_path.exists())
            content = report_path.read_text(encoding="utf-8")
            for section in ["## 主题概览", "## 热点聚类", "## 竞品套路", "## 受众痛点", "## 标题建议", "## 脚本大纲"]:
                self.assertIn(section, content)
            self.assertGreaterEqual(len(record.report["title_angles"]), 5)
            self.assertGreaterEqual(len(record.report["outline_suggestions"]), 3)

    def test_deduped_library_keeps_single_item_for_same_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            service = TopicScoutService(Repository(root))
            sample = ROOT / "tests" / "fixtures" / "sample_note.txt"
            service.ingest_file(str(sample))
            service.ingest_file(str(sample))
            library = json.loads((root / ".topic_scout" / "library.json").read_text(encoding="utf-8"))
            self.assertEqual(len(library), 1)

    def test_unsupported_file_type_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.docx"
            path.write_text("invalid", encoding="utf-8")
            with self.assertRaises(ContentExtractionError):
                load_file(str(path))
