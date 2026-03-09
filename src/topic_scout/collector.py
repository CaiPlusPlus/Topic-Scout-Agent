from __future__ import annotations

import csv
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import replace
from html.parser import HTMLParser

from .models import ContentItem
from .normalizer import clean_text, extract_keywords, normalize_platform


class ContentExtractionError(RuntimeError):
    pass


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.author: str | None = None
        self.keywords: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attr_map = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            content = attr_map.get("content")
            if not content:
                return
            if name in {"author", "article:author"}:
                self.author = content
            if name in {"keywords", "og:keywords"}:
                self.keywords.extend([part.strip() for part in content.split(",") if part.strip()])

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        snippet = data.strip()
        if not snippet:
            return
        if self.in_title:
            self.title_parts.append(snippet)
        self.text_parts.append(snippet)


def _new_item_id() -> str:
    return uuid.uuid4().hex[:12]


def _build_item(
    *,
    source_type: str,
    platform: str,
    url: str | None,
    title: str,
    author: str | None,
    published_at: str | None,
    tags: list[str],
    raw_text: str,
) -> ContentItem:
    cleaned = clean_text(raw_text)
    normalized_tags = tags or extract_keywords(cleaned)
    return ContentItem(
        id=_new_item_id(),
        source_type=source_type,
        platform=normalize_platform(platform),
        url=url,
        title=title or "Untitled",
        author=author,
        published_at=published_at,
        tags=normalized_tags,
        raw_text=raw_text.strip(),
        clean_text=cleaned,
    )


def load_file(path: str) -> list[ContentItem]:
    file_path = pathlib.Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = file_path.read_text(encoding="utf-8")
        return [
            _build_item(
                source_type="file",
                platform="generic",
                url=None,
                title=file_path.stem,
                author=None,
                published_at=None,
                tags=[],
                raw_text=text,
            )
        ]
    if suffix == ".csv":
        return _load_csv(file_path)
    if suffix == ".json":
        return _load_json(file_path)
    raise ContentExtractionError(f"Unsupported file type: {suffix}")


def _load_csv(path: pathlib.Path) -> list[ContentItem]:
    items: list[ContentItem] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            raw_text = row.get("raw_text") or row.get("content") or row.get("text") or ""
            if not raw_text.strip():
                continue
            items.append(
                _build_item(
                    source_type="file",
                    platform=row.get("platform") or "generic",
                    url=row.get("url"),
                    title=row.get("title") or f"{path.stem}-{index}",
                    author=row.get("author"),
                    published_at=row.get("published_at"),
                    tags=_split_tags(row.get("tags")),
                    raw_text=raw_text,
                )
            )
    if not items:
        raise ContentExtractionError("CSV file did not contain any usable content rows")
    return items


def _load_json(path: pathlib.Path) -> list[ContentItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload if isinstance(payload, list) else [payload]
    items: list[ContentItem] = []
    for index, row in enumerate(records, start=1):
        if not isinstance(row, dict):
            continue
        raw_text = str(row.get("raw_text") or row.get("content") or row.get("text") or "")
        if not raw_text.strip():
            continue
        items.append(
            _build_item(
                source_type="file",
                platform=str(row.get("platform") or "generic"),
                url=row.get("url"),
                title=str(row.get("title") or f"{path.stem}-{index}"),
                author=row.get("author"),
                published_at=row.get("published_at"),
                tags=_split_tags(row.get("tags")),
                raw_text=raw_text,
            )
        )
    if not items:
        raise ContentExtractionError("JSON file did not contain any usable content records")
    return items


def load_url(url: str, timeout: int = 10) -> ContentItem:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ContentExtractionError("URL must be a valid public http(s) address")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TopicScoutAgent/0.1 (+https://example.local/topic-scout)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        raise ContentExtractionError(f"Could not fetch URL: {url}") from exc
    parser = _HTMLTextExtractor()
    parser.feed(html)
    title = " ".join(parser.title_parts).strip() or parsed.netloc
    text = " ".join(parser.text_parts).strip()
    if not text:
        raise ContentExtractionError("Fetched page did not contain readable text")
    platform = _infer_platform_from_url(parsed.netloc)
    return _build_item(
        source_type="url",
        platform=platform,
        url=url,
        title=title,
        author=parser.author,
        published_at=None,
        tags=parser.keywords,
        raw_text=text,
    )


def _split_tags(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).replace("|", ",").split(",") if part.strip()]


def _infer_platform_from_url(netloc: str) -> str:
    lowered = netloc.lower()
    if "xiaohongshu" in lowered or "xhslink" in lowered:
        return "xiaohongshu"
    if "douyin" in lowered:
        return "douyin"
    return "generic"

