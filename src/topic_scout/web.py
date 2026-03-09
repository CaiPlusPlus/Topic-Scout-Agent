from __future__ import annotations

import html
import json
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .llm import LLMConfigurationError, LLMEnhancer
from .models import ResearchRequest
from .repository import Repository
from .service import TopicScoutService


class TopicScoutWebApp:
    def __init__(self, repository: Repository, llm_enhancer: LLMEnhancer | None = None) -> None:
        self.repository = repository
        self.service = TopicScoutService(repository, llm_enhancer=llm_enhancer)

    def render_home(self, flash: str | None = None) -> str:
        items = list(reversed(self.repository.load_items()))[:12]
        runs = self._load_recent_runs()
        stats = self._build_stats(items, runs)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Topic Scout</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffaf2;
      --ink: #1c1917;
      --muted: #6b5f53;
      --accent: #b45309;
      --accent-2: #1d4ed8;
      --line: #eadfcd;
      --card: rgba(255, 250, 242, 0.82);
    }}
    body {{ margin: 0; font-family: Georgia, "Hiragino Sans GB", serif; background:
      radial-gradient(circle at top, #fff7ed 0%, rgba(255,247,237,0.6) 18%, transparent 50%),
      linear-gradient(135deg, #f5f1e8 0%, #f3ece1 100%); color: var(--ink); }}
    .page {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 60px; }}
    .hero {{ display: grid; gap: 12px; margin-bottom: 28px; }}
    .hero h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3.4rem); line-height: 0.95; }}
    .hero p {{ margin: 0; color: var(--muted); max-width: 720px; }}
    .hero-bar {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .pill {{ display: inline-flex; align-items: center; border-radius: 999px; border: 1px solid var(--line); background: rgba(255,255,255,0.7); padding: 8px 12px; font-size: 0.92rem; color: var(--muted); }}
    .flash {{ background: #fffbeb; border: 1px solid #facc15; padding: 12px 14px; margin: 18px 0; border-radius: 12px; }}
    .stats {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); margin: 18px 0 26px; }}
    .stat {{ background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(255,248,240,0.95)); border: 1px solid var(--line); border-radius: 18px; padding: 18px; box-shadow: 0 18px 36px rgba(120, 53, 15, 0.08); }}
    .stat strong {{ display: block; font-size: 1.8rem; }}
    .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .panel {{ background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 18px; box-shadow: 0 16px 40px rgba(120, 53, 15, 0.06); backdrop-filter: blur(8px); }}
    h2, h3 {{ margin-top: 0; }}
    label {{ display: block; margin: 10px 0 6px; font-size: 0.95rem; color: var(--muted); }}
    input, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #d6c7b1; border-radius: 12px; padding: 11px 12px; background: #fff; font: inherit; }}
    textarea {{ min-height: 110px; resize: vertical; }}
    button {{ margin-top: 14px; border: none; border-radius: 999px; padding: 11px 18px; background: var(--accent); color: white; font: inherit; cursor: pointer; }}
    .secondary {{ background: var(--accent-2); }}
    ul {{ padding-left: 18px; margin-bottom: 0; }}
    .meta {{ color: var(--muted); font-size: 0.92rem; }}
    .report-link {{ display: inline-block; margin-top: 8px; }}
    .stack {{ display: grid; gap: 16px; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; }}
    .actions a {{ color: var(--accent-2); text-decoration: none; font-size: 0.95rem; }}
    .hint {{ margin-top: 8px; color: var(--muted); font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>Topic Scout<br>Minimal Web UI</h1>
      <p>复用现有 service 层，在浏览器里完成素材导入、选题研究和报告查看。默认仍然支持纯规则模式；勾选 LLM 时，会使用当前环境变量里的模型配置。</p>
      <div class="hero-bar">
        <span class="pill">AI 自动生成报告</span>
        <span class="pill">失败自动回退</span>
        <span class="pill">适合审核流</span>
      </div>
    </section>
    {self._render_flash(flash)}
    <section class="stats">
      <article class="stat"><strong>{stats["items"]}</strong><span>素材总数</span></article>
      <article class="stat"><strong>{stats["runs"]}</strong><span>研究报告</span></article>
      <article class="stat"><strong>{stats["platforms"]}</strong><span>活跃平台</span></article>
      <article class="stat"><strong>{stats["llm_ready"]}</strong><span>LLM 状态</span></article>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>生成研究报告</h2>
        <form method="post" action="/research">
          <label for="topic">主题</label>
          <input id="topic" name="topic" required placeholder="例如：AI 提效内容">
          <label for="audience">受众</label>
          <input id="audience" name="audience" value="独立创作者">
          <label for="tone">语气</label>
          <input id="tone" name="tone" value="专业但接地气">
          <label for="platforms">平台（逗号分隔）</label>
          <input id="platforms" name="platforms" placeholder="xiaohongshu,douyin">
          <label><input type="checkbox" name="use_llm" value="1"> 使用 LLM 增强</label>
          <button type="submit">生成报告</button>
          <p class="hint">研究完成后会保留运行记录，适合你只做最终审核。</p>
        </form>
      </article>
      <article class="panel stack">
        <div>
          <h2>导入本地文件</h2>
          <form method="post" action="/ingest/file">
            <label for="path">文件路径</label>
            <input id="path" name="path" required placeholder="/absolute/path/to/file.csv">
            <button type="submit">导入文件</button>
          </form>
        </div>
        <div>
          <h2>导入公开 URL</h2>
          <form method="post" action="/ingest/url">
            <label for="url">页面链接</label>
            <input id="url" name="url" required placeholder="https://...">
            <button type="submit">导入 URL</button>
          </form>
        </div>
        <div>
          <h2>粘贴素材</h2>
          <form method="post" action="/ingest/text">
            <label for="text_title">标题</label>
            <input id="text_title" name="title" placeholder="例如：用户评论摘录">
            <label for="text_platform">平台</label>
            <input id="text_platform" name="platform" placeholder="xiaohongshu">
            <label for="text_body">正文</label>
            <textarea id="text_body" name="text" required placeholder="直接粘贴评论、脚本或竞品内容"></textarea>
            <button class="secondary" type="submit">导入文本</button>
          </form>
        </div>
      </article>
    </section>
    <section class="grid" style="margin-top: 18px;">
      <article class="panel">
        <h3>最近素材</h3>
        <ul>
          {self._render_items(items)}
        </ul>
      </article>
      <article class="panel">
        <h3>最近报告</h3>
        <ul>
          {self._render_runs(runs)}
        </ul>
        <div class="actions">
          <a href="/api/library">查看素材 JSON</a>
          <a href="/api/runs">查看运行 JSON</a>
        </div>
      </article>
    </section>
  </div>
</body>
</html>"""

    def render_report(self, run_id: str) -> str:
        record = self.service.get_report(run_id)
        markdown = self._read_report(record.report_path)
        return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(record.topic)}</title>
<style>
body {{ margin: 0; background: #f8fafc; color: #111827; font-family: Georgia, "Hiragino Sans GB", serif; }}
.page {{ max-width: 920px; margin: 0 auto; padding: 28px 18px 40px; }}
a {{ color: #b45309; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px; line-height: 1.6; }}
</style></head>
<body><div class="page"><p><a href="/">返回首页</a></p><pre>{html.escape(markdown)}</pre></div></body></html>"""

    def handle_ingest_file(self, form_data: dict[str, list[str]]) -> str:
        path = _first_value(form_data, "path")
        items = self.service.ingest_file(path)
        return f"已导入 {len(items)} 条文件素材。"

    def handle_ingest_url(self, form_data: dict[str, list[str]]) -> str:
        url = _first_value(form_data, "url")
        item = self.service.ingest_url(url)
        return f"已导入 URL 素材：{item.title}"

    def handle_ingest_text(self, form_data: dict[str, list[str]]) -> str:
        title = _first_value(form_data, "title") or "web-note"
        platform = _first_value(form_data, "platform") or "generic"
        text = _first_value(form_data, "text")
        item = self.service.ingest_text(text=text, title=title, platform=platform)
        return f"已导入文本素材：{item.title}"

    def handle_research(self, form_data: dict[str, list[str]]) -> str:
        topic = _first_value(form_data, "topic")
        audience = _first_value(form_data, "audience") or "独立创作者"
        tone = _first_value(form_data, "tone") or "专业但接地气"
        platforms = [part.strip() for part in _first_value(form_data, "platforms").split(",") if part.strip()]
        use_llm = _first_value(form_data, "use_llm") == "1"
        request = ResearchRequest(
            topic=topic,
            platforms=platforms,
            source_ids=[],
            tone=tone,
            target_audience=audience,
            use_llm=use_llm,
        )
        record = self.service.research(request)
        return f'报告已生成：<a class="report-link" href="/report/{record.run_id}">{record.run_id}</a>'

    def _load_recent_runs(self):
        raw = self.repository._read_json(self.repository.runs_index_path, [])
        return list(reversed(raw[-10:]))

    def _read_report(self, report_path: str) -> str:
        path = Path(report_path)
        if not path.is_absolute():
            path = self.repository.root / path
        return path.read_text(encoding="utf-8")

    def render_library_json(self) -> str:
        payload = [item.to_dict() for item in self.repository.load_items()]
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def render_runs_json(self) -> str:
        payload = self.repository._read_json(self.repository.runs_index_path, [])
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _build_stats(self, items, runs) -> dict[str, str]:
        platforms = {item.platform for item in items if item.platform}
        llm_ready = "Ready" if self.service.llm_enhancer is not None else "Rule only"
        return {
            "items": str(len(self.repository.load_items())),
            "runs": str(len(runs)),
            "platforms": str(len(platforms) or 1),
            "llm_ready": llm_ready,
        }

    def _render_items(self, items) -> str:
        if not items:
            return "<li class='meta'>还没有素材，先导入一个文件或 URL。</li>"
        return "".join(
            f"<li><strong>{html.escape(item.title)}</strong><div class='meta'>{html.escape(item.platform)} · {html.escape(', '.join(item.tags[:4]))}</div></li>"
            for item in items
        )

    def _render_runs(self, runs) -> str:
        if not runs:
            return "<li class='meta'>还没有报告，先生成一次研究。</li>"
        return "".join(
            f"<li><a href='/report/{html.escape(run['run_id'])}'>{html.escape(run['topic'])}</a><div class='meta'>{html.escape(run['created_at'])}</div></li>"
            for run in runs
        )

    def _render_flash(self, flash: str | None) -> str:
        if not flash:
            return ""
        return f"<div class='flash'>{flash}</div>"


def serve(repository: Repository, host: str = "127.0.0.1", port: int = 8000) -> None:
    llm_enhancer = None
    try:
        llm_enhancer = LLMEnhancer.from_env()
    except LLMConfigurationError:
        llm_enhancer = None
    app = TopicScoutWebApp(repository, llm_enhancer=llm_enhancer)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._send_html(app.render_home())
                return
            if self.path.startswith("/report/"):
                run_id = self.path.removeprefix("/report/")
                try:
                    self._send_html(app.render_report(run_id))
                except FileNotFoundError as exc:
                    self._send_html(app.render_home(flash=html.escape(str(exc))), status=HTTPStatus.NOT_FOUND)
                return
            if self.path == "/api/library":
                self._send_json(app.render_library_json())
                return
            if self.path == "/api/runs":
                self._send_json(app.render_runs_json())
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            form_data = urllib.parse.parse_qs(raw_body)
            try:
                if self.path == "/ingest/file":
                    flash = app.handle_ingest_file(form_data)
                elif self.path == "/ingest/url":
                    flash = app.handle_ingest_url(form_data)
                elif self.path == "/ingest/text":
                    flash = app.handle_ingest_text(form_data)
                elif self.path == "/research":
                    flash = app.handle_research(form_data)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                self._send_html(app.render_home(flash=flash))
            except Exception as exc:  # pragma: no cover - defensive handler path
                self._send_html(app.render_home(flash=html.escape(str(exc))), status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args) -> None:
            return

        def _send_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Topic Scout Web UI running at http://{host}:{port}")
    server.serve_forever()


def _first_value(form_data: dict[str, list[str]], key: str) -> str:
    values = form_data.get(key, [""])
    return values[0].strip()
