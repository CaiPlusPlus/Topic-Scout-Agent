from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CLITestCase(unittest.TestCase):
    def run_cli(self, *args: str):
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "topic_scout.cli", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_ingest_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            sample = ROOT / "tests" / "fixtures" / "sample_note.txt"
            result = subprocess.run(
                [sys.executable, "-m", "topic_scout.cli", "ingest", "file", str(sample)],
                cwd=workspace,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Ingested 1 item(s)", result.stdout)

    def test_invalid_url_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            result = subprocess.run(
                [sys.executable, "-m", "topic_scout.cli", "ingest", "url", "notaurl"],
                cwd=workspace,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("valid public http(s) address", result.stderr)

    def test_report_command_shows_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            sample = ROOT / "tests" / "fixtures" / "sample_note.txt"
            ingest = subprocess.run(
                [sys.executable, "-m", "topic_scout.cli", "ingest", "file", str(sample)],
                cwd=workspace,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            research = subprocess.run(
                [sys.executable, "-m", "topic_scout.cli", "research", "效率选题"],
                cwd=workspace,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(research.returncode, 0, research.stderr)
            run_id = next(line.split(": ", 1)[1] for line in research.stdout.splitlines() if line.startswith("Run ID:"))
            report = subprocess.run(
                [sys.executable, "-m", "topic_scout.cli", "report", run_id.strip()],
                cwd=workspace,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn("Report Path:", report.stdout)

