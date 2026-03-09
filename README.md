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
- Persist reports under `runs/<timestamp>/report.md`
- View previously generated reports by run id

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
topic-scout ingest file ./examples/sample.txt
topic-scout research "职场效率" --audience "独立创作者"
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
```

## Storage

- Content library: `.topic_scout/library.json`
- Run metadata: `.topic_scout/runs.json`
- Markdown reports: `runs/<run_id>/report.md`

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The project uses only Python standard library modules so the MVP stays easy to run in a fresh environment.

