# Topic Scout Agent

Topic Scout Agent is a Python CLI for content marketers who need fast topic research for Xiaohongshu and Douyin style short-form content. It ingests local files or public URLs, normalizes the source material, analyzes recurring themes, and generates a Markdown report with title angles and outline suggestions.

## Features

- Ingest `txt`, `md`, `csv`, and `json` source files into a local content library
- Ingest a public URL and extract a best-effort title, author, tags, and body text
- Generate a research report with six fixed sections:
  - 主题概览
  - 热点聚类
  - 竞品套路
  - 受众痛点
  - 标题建议
  - 脚本大纲
- Optionally enhance the research report with an OpenAI-compatible LLM
- Switch between `openai-compatible` and `ollama` providers
- Run a minimal Web UI on top of the same service layer
- Persist reports under `runs/<timestamp>/report.md`
- View previously generated reports by run id

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
topic-scout ingest file ./examples/sample.txt
topic-scout research "职场效率" --audience "独立创作者"
topic-scout research "职场效率" --audience "独立创作者" --llm
topic-scout serve --host 127.0.0.1 --port 8000
```

If you do not want to install the package yet, you can run the module directly:

```bash
PYTHONPATH=src python3 -m topic_scout.cli ingest file ./examples/sample.txt
```

## CLI

```bash
topic-scout ingest file <path>
topic-scout ingest url <url>
topic-scout research <topic> [--platform xiaohongshu --platform douyin] [--source-id <id>] [--audience <value>] [--tone <value>]
topic-scout report <run_id>
topic-scout serve [--host 127.0.0.1] [--port 8000]
```

Enable LLM enhancement by setting environment variables and passing `--llm`:

```bash
export TOPIC_SCOUT_API_KEY=...
export TOPIC_SCOUT_MODEL=gpt-4.1-mini
export TOPIC_SCOUT_API_BASE=https://api.openai.com/v1
export TOPIC_SCOUT_LLM_PROVIDER=openai-compatible
export TOPIC_SCOUT_PROMPT_TEMPLATE=default-v1
topic-scout research "职场效率" --llm
```

For local models through Ollama:

```bash
export TOPIC_SCOUT_LLM_PROVIDER=ollama
export TOPIC_SCOUT_MODEL=qwen2.5:7b
export TOPIC_SCOUT_API_BASE=http://127.0.0.1:11434
topic-scout research "职场效率" --llm
```

`TOPIC_SCOUT_API_BASE` is optional and defaults to the provider-specific endpoint root. The Web UI will also try to reuse the same LLM config when available.

## Storage

- Content library: `.topic_scout/library.json`
- Run metadata: `.topic_scout/runs.json`
- Markdown reports: `runs/<run_id>/report.md`

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The project uses only Python standard library modules so the MVP stays easy to run in a fresh environment.
