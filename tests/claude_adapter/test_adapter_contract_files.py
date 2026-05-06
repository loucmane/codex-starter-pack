from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_NUDGE = REPO_ROOT / ".claude" / "scripts" / "handoff-nudge.sh"


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


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


def test_claude_entrypoint_defines_gated_runtime() -> None:
    text = read("CLAUDE.md")

    assert "gated participant" in text
    assert "bash .claude/scripts/readiness.sh" in text
    assert "PreToolUse dispatcher" in text
    assert "Multimodal Scope" in text
    assert "CODEX.md" in text
    assert "templates/**" in text


def test_settings_registers_pretooluse_and_stop_hooks() -> None:
    settings = json.loads(read(".claude/settings.json"))
    hooks = settings["hooks"]

    pretool = hooks["PreToolUse"][0]
    assert pretool["matcher"] == "Edit|Write|MultiEdit|NotebookEdit|Bash"
    assert pretool["hooks"][0]["command"] == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/pretooluse-gate.sh"
    assert hooks["Stop"][0]["hooks"][0]["command"] == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/handoff-nudge.sh"


def test_runtime_commands_exist_and_wrap_expected_helpers() -> None:
    expected = {
        "readiness.md": "bash .claude/scripts/readiness.sh",
        "kickoff.md": "python3 scripts/codex-task wizard kickoff",
        "guard.md": "python3 scripts/codex-guard validate",
        "plan-sync.md": "python3 scripts/codex-task plan sync",
        "work-tracking-audit.md": "python3 scripts/codex-task work-tracking audit",
        "sessions-update.md": "python3 scripts/codex-task sessions update",
        "work-tracking-update.md": "python3 scripts/codex-task work-tracking update",
        "scanner-run.md": "python3 scripts/codex-task scanner run",
    }
    for filename, needle in expected.items():
        text = read(f".claude/commands/{filename}")
        assert needle in text
        assert "allowed-tools: Bash" in text


def test_agents_require_readiness_and_audit_trail() -> None:
    for path in [
        ".claude/agents/task-executor.md",
        ".claude/agents/task-orchestrator.md",
        ".claude/agents/task-checker.md",
    ]:
        text = read(path)
        assert "bash .claude/scripts/readiness.sh" in text
        assert "BLOCKED" in text
        assert "CODEX.md" in text

    assert "S:W:H:E" in read(".claude/agents/task-executor.md")
    assert "Delegation Brief" in read(".claude/agents/task-orchestrator.md")
    assert "audit_trail" in read(".claude/agents/task-checker.md")


def test_agents_catalog_names_runtime_components() -> None:
    text = read(".claude/AGENTS.md")

    assert ".claude/scripts/pretooluse-gate.sh" in text
    assert ".claude/scripts/handoff-nudge.sh" in text
    assert "task-executor" in text
    assert "task-orchestrator" in text
    assert "task-checker" in text


def test_handoff_nudge_warns_for_dirty_workflow_state_without_blocking(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert run(["git", "init", "-q"], repo).returncode == 0
    (repo / "sessions").mkdir()
    (repo / "sessions" / "scratch.md").write_text("dirty workflow state\n", encoding="utf-8")

    result = run(
        ["bash", str(HANDOFF_NUDGE)],
        repo,
        input_text="{}",
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)},
    )

    assert result.returncode == 0
    assert "dirty workflow-state file" in result.stderr


def test_tool_mapping_preserves_shared_files() -> None:
    text = read(".claude/engine/tool-mapping.md")

    assert "Do not edit shared handlers or templates to rename tools" in text
    assert "scripts/codex-task" in text
    assert "scripts/codex-guard" in text
