# Topic Scout Agent

[中文文档](README.zh-CN.md)

Topic Scout Agent is a Python-based research agent for creators and content operators who need fast topic discovery for Xiaohongshu and Douyin style short-form content. It reuses one shared service layer across CLI, Web UI, CI workflows, and issue-driven automation.

## Features

- Ingest `txt`, `md`, `csv`, and `json` files into a local content library
- Ingest a public URL and extract title, author, tags, and readable body text
- Paste raw content directly in the Web UI for faster review workflows
- Generate a fixed-structure research report with:
  - topic summary
  - trend clusters
  - competitor patterns
  - pain points
  - title angles
  - outline suggestions
- Optionally enhance reports with an LLM
- Switch between `openai-compatible` and `ollama` providers
- Fall back to deterministic planner output if the LLM fails
- Run a minimal Web UI and deployment entrypoint from the same service layer
- Support GitHub CI, Render deployment, and issue-triggered autofix workflows

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
topic-scout ingest file ./tests/fixtures/sample_note.txt
topic-scout research "content efficiency" --audience "independent creators"
topic-scout serve --host 127.0.0.1 --port 8000
python -m topic_scout.deploy
```

Run directly without installation:

```bash
PYTHONPATH=src python3 -m topic_scout.cli research "content efficiency"
```

## CLI

```bash
topic-scout ingest file <path>
topic-scout ingest url <url>
topic-scout research <topic> [--platform xiaohongshu --platform douyin] [--source-id <id>] [--audience <value>] [--tone <value>] [--llm]
topic-scout report <run_id>
topic-scout serve [--host 127.0.0.1] [--port 8000]
```

## LLM Configuration

For OpenAI-compatible providers:

```bash
export TOPIC_SCOUT_API_KEY=...
export TOPIC_SCOUT_MODEL=gpt-4.1-mini
export TOPIC_SCOUT_API_BASE=https://api.openai.com/v1
export TOPIC_SCOUT_LLM_PROVIDER=openai-compatible
export TOPIC_SCOUT_PROMPT_TEMPLATE=default-v1
topic-scout research "content efficiency" --llm
```

For Ollama:

```bash
export TOPIC_SCOUT_LLM_PROVIDER=ollama
export TOPIC_SCOUT_MODEL=qwen2.5:7b
export TOPIC_SCOUT_API_BASE=http://127.0.0.1:11434
topic-scout research "content efficiency" --llm
```

Supported prompt templates:

- `default-v1`
- `hook-heavy-v1`

## Web UI

- Browser home: `/`
- Recent materials JSON: `/api/library`
- Recent runs JSON: `/api/runs`
- Paste-source ingestion is available directly in the page

## Storage

- Content library: `.topic_scout/library.json`
- Run metadata: `.topic_scout/runs.json`
- Markdown reports: `runs/<run_id>/report.md`

## CI/CD And Deployment

- CI workflow: [`.github/workflows/ci.yml`](/Users/itlc00010/.codex/worktrees/1122/Playground/.github/workflows/ci.yml)
- Render deployment trigger: [`.github/workflows/deploy-render.yml`](/Users/itlc00010/.codex/worktrees/1122/Playground/.github/workflows/deploy-render.yml)
- Issue autofix workflow: [`.github/workflows/issue-autofix.yml`](/Users/itlc00010/.codex/worktrees/1122/Playground/.github/workflows/issue-autofix.yml)
- Docker image: [Dockerfile](/Users/itlc00010/.codex/worktrees/1122/Playground/Dockerfile)
- Render blueprint: [render.yaml](/Users/itlc00010/.codex/worktrees/1122/Playground/render.yaml)

Required GitHub secrets:

- `RENDER_DEPLOY_HOOK_URL`
- `AUTOFIX_API_KEY`
- `AUTOFIX_MODEL`
- `AUTOFIX_API_BASE` (optional for OpenAI-compatible backends)

Autofix flow:

1. Open a bug issue from the template.
2. Add the `autofix` label when AI should attempt a repair.
3. GitHub Actions creates a fix branch, runs tests, and opens a draft PR for review.

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The project intentionally stays close to the Python standard library so the local setup remains simple and automation-friendly.

