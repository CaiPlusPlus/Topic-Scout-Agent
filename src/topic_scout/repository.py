from __future__ import annotations

import json
from pathlib import Path

from .models import ContentItem, RunRecord


class Repository:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or ".")
        self.data_dir = self.root / ".topic_scout"
        self.library_path = self.data_dir / "library.json"
        self.runs_index_path = self.data_dir / "runs.json"
        self.runs_dir = self.root / "runs"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def load_items(self) -> list[ContentItem]:
        payload = self._read_json(self.library_path, [])
        return [ContentItem.from_dict(item) for item in payload]

    def save_items(self, items: list[ContentItem]) -> None:
        self._write_json(self.library_path, [item.to_dict() for item in items])

    def append_items(self, new_items: list[ContentItem]) -> list[ContentItem]:
        items = self.load_items()
        items.extend(new_items)
        self.save_items(items)
        return items

    def save_run(self, record: RunRecord) -> None:
        runs = self._read_json(self.runs_index_path, [])
        runs.append(record.to_dict())
        self._write_json(self.runs_index_path, runs)

    def load_run(self, run_id: str) -> RunRecord | None:
        runs = self._read_json(self.runs_index_path, [])
        for raw in runs:
            if raw.get("run_id") == run_id:
                return RunRecord.from_dict(raw)
        return None

    def write_report(self, run_id: str, content: str) -> Path:
        report_dir = self.runs_dir / run_id
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "report.md"
        report_path.write_text(content, encoding="utf-8")
        return report_path

    def _read_json(self, path: Path, default):
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

