"""Plan mode must deny mutation, not merely withhold native approval."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_foundation.gate.hooks import decisions, permission_modes, pretool
from test_native_command_profile import (
    CONTEXT_REL,
    ENV,
    SCOPED,
    WORKFLOW_REL,
    event,
    git,
    managed_repo,
)
from test_pretooluse_gates import PRETOOLUSE, read_gate_decisions, run, run_gate, write


@pytest.fixture(autouse=True)
def isolate_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-host-config"))
    monkeypatch.delenv("AEGIS_INVOKING_AGENT", raising=False)


def set_advisory(repo: Path, advisory: bool) -> None:
    if advisory:
        write(repo / ".aegis/state/enforcement.json", '{"mode":"advisory"}')


def assert_plan_denial(result: object, repo: Path) -> None:
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert "plan mode" in result.stderr.lower()
    assert '"permissionDecision": "allow"' not in result.stdout
    records = read_gate_decisions(repo)
    assert len(records) == 1
    assert records[0]["verdict"] == "block"
    assert records[0]["reason"] == "plan_mode_mutation"
    assert len(records[0]["payload_digest"]) == 64


@pytest.mark.parametrize("ready", [False, True])
@pytest.mark.parametrize("advisory", [False, True])
def test_plan_begin_denies_before_client_can_execute(
    tmp_path: Path, ready: bool, advisory: bool
) -> None:
    repo = managed_repo(tmp_path, ready=ready)
    # A deliberately harmless synthetic entrypoint lets the test model the real
    # client's "exit zero means proceed" behavior without touching a real store.
    write(
        repo / WORKFLOW_REL,
        "from pathlib import Path\nPath('executed-marker').write_text('executed')\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "synthetic executable probe")
    set_advisory(repo, advisory)
    before = run(["git", "status", "--porcelain"], repo).stdout
    command = f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-fixture"
    result = run_gate(PRETOOLUSE, repo, event(repo, command, permission_mode="plan"))
    if result.returncode == 0:
        executed = run(
            [
                "python3",
                str(repo / WORKFLOW_REL),
                "begin",
                "--root",
                str(repo),
                "--bead",
                "ga-fixture",
            ],
            repo,
        )
        assert executed.returncode == 0, executed.stderr
    assert not (repo / "executed-marker").exists(), "plan-mode tool actually executed"
    assert run(["git", "status", "--porcelain"], repo).stdout == before
    assert not (repo / ".git/gas-city-workflow/transactions").exists()
    assert not (repo.parent / (repo.name + "-worktrees")).exists()
    assert_plan_denial(result, repo)


@pytest.mark.parametrize("advisory", [False, True])
@pytest.mark.parametrize(
    "tool_name,tool_input",
    [
        ("Write", {"file_path": "plans/new.md", "content": "no plan-write exemption"}),
        ("Edit", {"file_path": "README.md", "old_string": "a", "new_string": "b"}),
        ("MultiEdit", {"file_path": "README.md", "edits": []}),
        ("NotebookEdit", {"notebook_path": "example.ipynb", "new_source": "x"}),
        ("apply_patch", {"command": "*** Begin Patch\n*** Add File: x\n+x\n*** End Patch"}),
        ("Bash", {"command": "./.aegis/bin/aegis observe start --target-dir ."}),
        ("Bash", {"command": "./.aegis/bin/aegis log --note changed"}),
        ("Bash", {"command": SCOPED + " update ga-fixture --status in_progress"}),
        ("Bash", {"command": "git status --short && touch forbidden"}),
        ("Bash", {"command": "unknown-command"}),
        ("Bash", {}),
        ("mcp__aegis__kickoff", {"task_id": "ga-fixture"}),
        ("mcp__aegis__repair", {"apply": True}),
        ("mcp__unknown__operation", {}),
        ("Agent", {"prompt": "work", "description": "fixture"}),
        ("Task", {"prompt": "work", "description": "fixture"}),
    ],
)
def test_plan_mode_precedes_workflow_exemptions_and_delegation(
    tmp_path: Path, advisory: bool, tool_name: str, tool_input: dict[str, object]
) -> None:
    repo = managed_repo(tmp_path, ready=True)
    set_advisory(repo, advisory)
    data = json.dumps(
        {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "permission_mode": "plan",
            "cwd": str(repo),
        }
    )
    assert_plan_denial(run_gate(PRETOOLUSE, repo, data), repo)
    assert not (repo / "plans/new.md").exists()
    assert not (repo / "forbidden").exists()


@pytest.mark.parametrize("kind", ["context", "bead", "git", "read", "mcp-read"])
def test_plan_mode_keeps_existing_read_only_inspection(tmp_path: Path, kind: str) -> None:
    repo = managed_repo(tmp_path)
    data = {
        "context": event(
            repo, f"python3 {repo / CONTEXT_REL} --root {repo} --check", permission_mode="plan"
        ),
        "bead": event(repo, ENV + SCOPED + " show ga-fixture --json", permission_mode="plan"),
        "git": event(repo, "git status --short", permission_mode="plan"),
        "read": json.dumps(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": "README.md"},
                "permission_mode": "plan",
            }
        ),
        "mcp-read": json.dumps(
            {"tool_name": "mcp__aegis__status", "tool_input": {}, "permission_mode": "plan"}
        ),
    }[kind]
    result = run_gate(PRETOOLUSE, repo, data)
    assert result.returncode == 0, result.stderr
    assert all(row["verdict"] != "block" for row in read_gate_decisions(repo))


@pytest.mark.parametrize("advisory", [False, True])
def test_degraded_fallback_cannot_allow_plan_begin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, advisory: bool
) -> None:
    repo = managed_repo(tmp_path)
    set_advisory(repo, advisory)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    data = event(
        repo,
        f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-fixture",
        permission_mode="plan",
    )
    rc = pretool.degraded_pretooluse_fallback(data, RuntimeError("synthetic failure"))
    assert rc == 2
    assert read_gate_decisions(repo)[0]["reason"] == "plan_mode_mutation"
    assert not (repo / ".aegis/state/degraded-events.json").exists()


def test_plan_denial_precedes_readiness_and_delegation_processing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = managed_repo(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))

    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("plan-mode mutation reached a later gate stage")

    monkeypatch.setattr(pretool, "run_readiness", unexpected)
    monkeypatch.setattr(pretool, "evaluate_native_delegation", unexpected)
    data = event(
        repo,
        f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-fixture",
        permission_mode="plan",
    )
    assert pretool.pretooluse_gate(data) == 2


@pytest.mark.parametrize("degraded", [False, True])
@pytest.mark.parametrize("failure", ["classifier", "audit"])
def test_plan_boundary_stays_closed_on_infrastructure_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, degraded: bool, failure: str
) -> None:
    repo = managed_repo(tmp_path)
    set_advisory(repo, True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic unavailable infrastructure")

    if failure == "classifier":
        monkeypatch.setattr(permission_modes, "payload_is_read_only", fail)
    else:
        monkeypatch.setattr(decisions, "append_gate_decision", fail)
    data = event(
        repo,
        f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-fixture",
        permission_mode="plan",
    )
    rc = (
        pretool.degraded_pretooluse_fallback(data, RuntimeError("upstream failure"))
        if degraded
        else pretool.pretooluse_gate(data)
    )
    assert rc == 2
    assert not (repo / ".aegis/state/degraded-events.json").exists()


def test_plan_boundary_does_not_consume_a_workflow_override(tmp_path: Path) -> None:
    repo = managed_repo(tmp_path)
    token = repo / ".aegis/state/override-token.json"
    before = '{"reason_class":"any","reason":"synthetic workflow override"}'
    write(token, before)
    data = event(
        repo,
        f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-fixture",
        permission_mode="plan",
    )
    result = run_gate(PRETOOLUSE, repo, data)
    assert_plan_denial(result, repo)
    assert "NOT override-eligible" in result.stderr
    assert token.read_text() == before
