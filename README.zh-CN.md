# Topic Scout Agent

[English README](README.md)

Topic Scout Agent 是一个面向创作者和内容运营的 Python 研究型 Agent，主要服务小红书、抖音这类短内容场景。它复用同一套 service 层，贯通 CLI、Web UI、CI 工作流和 issue 自动修复流程，适合“AI 自动执行，人只做审核”的协作模式。

## 功能概览

- 导入 `txt`、`md`、`csv`、`json` 文件到本地素材库
- 导入公开 URL，并抽取标题、作者、标签和可读正文
- 直接在 Web 页面粘贴素材，降低审核和试用门槛
- 生成固定结构的选题研究报告，包括：
  - 主题概览
  - 热点聚类
  - 竞品套路
  - 受众痛点
  - 标题建议
  - 脚本大纲
- 可选接入 LLM 增强报告质量
- 支持 `openai-compatible` 与 `ollama` 两类提供商切换
- LLM 失败时自动回退到规则规划结果
- Web UI 与部署入口复用同一套服务逻辑
- 支持 GitHub CI、Render 部署和 issue 触发的自动修复流程

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
topic-scout ingest file ./tests/fixtures/sample_note.txt
topic-scout research "内容效率" --audience "独立创作者"
topic-scout serve --host 127.0.0.1 --port 8000
python -m topic_scout.deploy
```

如果暂时不安装，也可以直接运行：

```bash
PYTHONPATH=src python3 -m topic_scout.cli research "内容效率"
```

## CLI

```bash
topic-scout ingest file <path>
topic-scout ingest url <url>
topic-scout research <topic> [--platform xiaohongshu --platform douyin] [--source-id <id>] [--audience <value>] [--tone <value>] [--llm]
topic-scout report <run_id>
topic-scout serve [--host 127.0.0.1] [--port 8000]
```

## LLM 配置

使用 OpenAI 兼容接口：

```bash
export TOPIC_SCOUT_API_KEY=...
export TOPIC_SCOUT_MODEL=gpt-4.1-mini
export TOPIC_SCOUT_API_BASE=https://api.openai.com/v1
export TOPIC_SCOUT_LLM_PROVIDER=openai-compatible
export TOPIC_SCOUT_PROMPT_TEMPLATE=default-v1
topic-scout research "内容效率" --llm
```

使用 Ollama：

```bash
export TOPIC_SCOUT_LLM_PROVIDER=ollama
export TOPIC_SCOUT_MODEL=qwen2.5:7b
export TOPIC_SCOUT_API_BASE=http://127.0.0.1:11434
topic-scout research "内容效率" --llm
```

支持的提示词模板：

- `default-v1`
- `hook-heavy-v1`

## Web UI

- 首页：`/`
- 素材 JSON：`/api/library`
- 运行记录 JSON：`/api/runs`
- 页面内支持直接粘贴素材

## 存储结构

- 素材库：`.topic_scout/library.json`
- 运行索引：`.topic_scout/runs.json`
- Markdown 报告：`runs/<run_id>/report.md`

## CI/CD 与部署

- CI 工作流： [`.github/workflows/ci.yml`](/Users/itlc00010/.codex/worktrees/1122/Playground/.github/workflows/ci.yml)
- Render 部署触发： [`.github/workflows/deploy-render.yml`](/Users/itlc00010/.codex/worktrees/1122/Playground/.github/workflows/deploy-render.yml)
- Issue 自动修复工作流： [`.github/workflows/issue-autofix.yml`](/Users/itlc00010/.codex/worktrees/1122/Playground/.github/workflows/issue-autofix.yml)
- Docker 镜像入口： [Dockerfile](/Users/itlc00010/.codex/worktrees/1122/Playground/Dockerfile)
- Render 蓝图： [render.yaml](/Users/itlc00010/.codex/worktrees/1122/Playground/render.yaml)

GitHub Secrets 需要配置：

- `RENDER_DEPLOY_HOOK_URL`
- `AUTOFIX_API_KEY`
- `AUTOFIX_MODEL`
- `AUTOFIX_API_BASE`（OpenAI 兼容后端可选）

自动修复流程：

1. 使用 issue 模板提交 bug。
2. 当你希望 AI 自动尝试修复时，给 issue 加上 `autofix` 标签。
3. GitHub Actions 会生成修复分支、执行测试，并创建草稿 PR 供你审核。

## 开发与测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

这个项目刻意尽量使用 Python 标准库，目标是让本地环境、CI 和自动化修复流程都保持简单、稳定、易审计。

