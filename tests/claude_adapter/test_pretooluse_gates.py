from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PRETOOLUSE = REPO_ROOT / ".claude" / "scripts" / "pretooluse-gate.sh"
PATH_GUARD = REPO_ROOT / ".claude" / "scripts" / "codex-path-guard.sh"
BASH_GUARD = REPO_ROOT / ".claude" / "scripts" / "bash-command-guard.sh"


def run(cmd: list[str], cwd: Path, *, input_text: str = "", env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def payload(tool_name: str, **tool_input: str) -> str:
    return json.dumps({"tool_name": tool_name, "tool_input": tool_input})


def make_repo(tmp_path: Path, *, ready: bool) -> Path:
    repo = tmp_path / ("ready-repo" if ready else "blocked-repo")
    repo.mkdir()
    assert run(["git", "init", "-q"], repo).returncode == 0
    branch = "feat/task-103-claude-runtime-adapter" if ready else "feature/no-task"
    assert run(["git", "checkout", "-q", "-b", branch], repo).returncode == 0
    if not ready:
        return repo

    write(
        repo / ".taskmaster" / "tasks" / "tasks.json",
        json.dumps({"master": {"tasks": [{"id": 103, "title": "Claude Runtime Adapter", "status": "in-progress"}]}}),
    )
    session_rel = Path("2026/05/2026-05-06-002-task103-claude-runtime-adapter.md")
    write(repo / "sessions" / session_rel, "# Task 103 Session\n")
    (repo / "sessions" / "current").symlink_to(session_rel)
    write(
        repo / "sessions" / "state.json",
        json.dumps({"current": session_rel.name, "paused": [], "updated_at": "2026-05-06T17:35:54+02:00"}),
    )
    plan_rel = Path("2026-05-06-task103-claude-runtime-adapter.md")
    write(
        repo / "plans" / plan_rel,
        """---
task_ids: [103]
---

# Plan - Task 103

| Step ID | Description | Evidence | Status |
| --- | --- | --- | --- |
| plan-step-scope | Scope | evidence | completed |
| plan-step-implement | Implement | evidence | pending |
| plan-step-verify | Verify | evidence | pending |
""",
    )
    (repo / "plans" / "current").symlink_to(plan_rel)
    active = repo / "docs" / "ai" / "work-tracking" / "active" / "20260506-task103-claude-runtime-adapter-ACTIVE"
    write(
        active / "TRACKER.md",
        """# Task 103 Claude Runtime Adapter Tracker

## Plan Compliance Checklist
- [x] plan-step-scope - Scope
- [ ] plan-step-implement - Implement
- [ ] plan-step-verify - Verify
""",
    )
    return repo


def gate_env(repo: Path) -> dict[str, str]:
    import os

    return {**os.environ, "CLAUDE_PROJECT_DIR": str(repo)}


def run_gate(script: Path, repo: Path, hook_payload: str) -> subprocess.CompletedProcess[str]:
    return run(["bash", str(script)], repo, input_text=hook_payload, env=gate_env(repo))


def test_pretooluse_blocks_file_write_when_readiness_blocked(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)

    result = run_gate(PRETOOLUSE, repo, payload("Write", file_path="README.md"))

    assert result.returncode == 2
    assert "readiness is BLOCKED" in result.stderr
    assert "branch 'feature/no-task' does not contain a task ID" in result.stderr


def test_pretooluse_allows_read_only_bash_when_readiness_blocked(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)

    result = run_gate(PRETOOLUSE, repo, payload("Bash", command="git status --short"))

    assert result.returncode == 0
    assert result.stderr == ""


def test_pretooluse_blocks_bash_mutation_when_readiness_blocked(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)

    result = run_gate(PRETOOLUSE, repo, payload("Bash", command="echo x > README.md"))

    assert result.returncode == 2
    assert "readiness is BLOCKED" in result.stderr


def test_pretooluse_blocks_codex_owned_file_when_ready(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(PRETOOLUSE, repo, payload("Edit", file_path="CODEX.md"))

    assert result.returncode == 2
    assert "Protected path" in result.stderr
    assert "CODEX.md" in result.stderr


def test_pretooluse_allows_claude_owned_file_when_ready(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(PRETOOLUSE, repo, payload("Write", file_path=".claude/commands/readiness.md"))

    assert result.returncode == 0
    assert result.stderr == ""


def test_pretooluse_blocks_bash_redirect_to_codex_path_when_ready(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(PRETOOLUSE, repo, payload("Bash", command="printf 'x' > CODEX.md"))

    assert result.returncode == 2
    assert "redirection targets protected path CODEX.md" in result.stderr


def test_pretooluse_blocks_bash_sed_i_template_when_ready(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(PRETOOLUSE, repo, payload("Bash", command="sed -i 's/a/b/' templates/foo.md"))

    assert result.returncode == 2
    assert "sed -i targets protected path templates/foo.md" in result.stderr


def test_pretooluse_allows_safe_read_only_bash_when_ready(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(PRETOOLUSE, repo, payload("Bash", command="cat sessions/state.json"))

    assert result.returncode == 0
    assert result.stderr == ""


def test_path_guard_blocks_direct_protected_file_payload(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(PATH_GUARD, repo, payload("Write", file_path="templates/runtime.md"))

    assert result.returncode == 2
    assert "templates/runtime.md" in result.stderr


def test_bash_guard_blocks_python_open_write_to_protected_path(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=True)

    result = run_gate(BASH_GUARD, repo, payload("Bash", command="python3 -c \"open('scripts/codex-task','w').write('x')\""))

    assert result.returncode == 2
    assert "scripts/codex-task" in result.stderr
