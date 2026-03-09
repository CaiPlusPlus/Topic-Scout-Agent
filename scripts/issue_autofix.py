from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
ALLOWED_PREFIXES = ("src/", "tests/", ".github/", "README.md", "pyproject.toml")


def main() -> int:
    issue_number = os.getenv("ISSUE_NUMBER", "").strip()
    issue_title = os.getenv("ISSUE_TITLE", "").strip() or f"Issue {issue_number}"
    issue_body = os.getenv("ISSUE_BODY", "").strip()
    api_key = os.getenv("AUTOFIX_API_KEY", "").strip()
    model = os.getenv("AUTOFIX_MODEL", "").strip()
    api_base = os.getenv("AUTOFIX_API_BASE", "https://api.openai.com/v1").rstrip("/")

    if not issue_number:
        raise SystemExit("ISSUE_NUMBER is required")
    if not api_key or not model:
        _comment_on_issue(
            issue_number,
            "Autofix skipped: `AUTOFIX_API_KEY` or `AUTOFIX_MODEL` is missing in repository secrets."
        )
        return 0

    proposal = _request_patch_proposal(issue_title, issue_body, model, api_key, api_base)
    changed_paths = _apply_proposal(proposal)
    if not changed_paths:
        _comment_on_issue(issue_number, "Autofix finished with no file changes proposed.")
        return 0

    _run(["python", "-m", "unittest", "discover", "-s", "tests", "-v"])
    branch_name = f"codex/issue-{issue_number}-autofix"
    _run(["git", "checkout", "-B", branch_name])
    _run(["git", "add", *changed_paths])
    commit_message = proposal.get("commit_message") or f"Autofix issue #{issue_number}"
    _run(["git", "commit", "-m", commit_message])
    _run(["git", "push", "-u", "origin", branch_name, "--force-with-lease"])
    pr_body = proposal.get("summary", "Automated fix generated from issue context.")
    _run(
        [
            "gh",
            "pr",
            "create",
            "--draft",
            "--title",
            f"Autofix #{issue_number}: {issue_title}",
            "--body",
            f"{pr_body}\n\nCloses #{issue_number}",
            "--base",
            "main",
            "--head",
            branch_name,
        ]
    )
    return 0


def _request_patch_proposal(issue_title: str, issue_body: str, model: str, api_key: str, api_base: str) -> dict:
    files = _collect_repo_context()
    system = (
        "You are a senior Python engineer. Return strict JSON with keys "
        "`summary`, `commit_message`, and `files`. `files` must be a list of objects with `path` and `content`."
    )
    user = json.dumps(
        {
            "issue": {"title": issue_title, "body": issue_body},
            "repo_files": files,
            "constraints": {
                "only_touch_existing_or_new_repo_files": True,
                "allowed_prefixes": list(ALLOWED_PREFIXES),
                "must_keep_tests_passing": True,
            },
        },
        ensure_ascii=False,
    )
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = json.loads(response.read().decode("utf-8"))
    content = raw["choices"][0]["message"]["content"]
    return json.loads(content)


def _collect_repo_context() -> list[dict[str, str]]:
    result = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_dir() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if not rel.startswith(ALLOWED_PREFIXES):
            continue
        if path.suffix not in {".py", ".md", ".toml", ".yml", ".yaml"}:
            continue
        result.append({"path": rel, "content": path.read_text(encoding="utf-8")})
    return result


def _apply_proposal(proposal: dict) -> list[str]:
    changed = []
    for file_change in proposal.get("files", []):
        path = file_change["path"]
        if not path.startswith(ALLOWED_PREFIXES):
            raise RuntimeError(f"Refusing to write outside allowed prefixes: {path}")
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_change["content"], encoding="utf-8")
        changed.append(path)
    return changed


def _comment_on_issue(issue_number: str, body: str) -> None:
    repo = os.getenv("GITHUB_REPOSITORY", "").strip()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        return
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30):
        return


def _run(cmd: list[str]) -> None:
    completed = subprocess.run(cmd, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
