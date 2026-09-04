"""Native Claude approval is narrower than passing the Aegis gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_pretooluse_gates import PRETOOLUSE, REPO_ROOT, make_repo, run, run_gate, write

PROFILE = Path(".claude/orchestrator-command-profile.json")
SCOPED = "/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd"
ENV = (
    "/usr/bin/env -u BEADS_DIR -u BEADS_DB GC_HOME=/home/loucmane/gascity/home "
    "PATH=/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin "
)
WORKFLOW = REPO_ROOT / "plugins/gas-city-workflow/scripts/workflow.py"
CONTEXT = REPO_ROOT / "plugins/gas-city-workflow/scripts/project_context.py"
WORKFLOW_REL = WORKFLOW.relative_to(REPO_ROOT)
CONTEXT_REL = CONTEXT.relative_to(REPO_ROOT)


def git(repo: Path, *args: str) -> None:
    result = run(["git", "-c", "commit.gpgsign=false", *args], repo)
    assert result.returncode == 0, result.stderr


def profile(repo: Path) -> dict[str, object]:
    return {
        "schema": "aegis.claude-orchestrator-command-profile.v1",
        "project_id": "fixture-project",
        "canonical_root": str(repo),
        "worktree_root": str(repo.parent / (repo.name + "-worktrees")),
        "city": "/home/loucmane/gascity/city",
        "rig": "gascity",
        "commands": ["project-context", "beads-read", "workflow-begin"],
    }


def managed_repo(tmp_path: Path, *, ready: bool = False) -> Path:
    repo = make_repo(tmp_path, ready=ready)
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "remote", "add", "origin", "git@github.com:example/fixture-project.git")
    write(repo / ".gitignore", ".aegis/\n")
    write(
        repo / ".gas-city-workflow.json",
        json.dumps(
            {
                "schema": "gas-city-workflow.project.v1",
                "id": "fixture-project",
                "repository": "example/fixture-project",
                "rig": "gascity",
                "workflow_authority": "beads",
                "workflow_profile": "beads-with-aegis-evidence",
            }
        ),
    )
    write(repo / PROFILE, json.dumps(profile(repo)))
    write(repo / WORKFLOW_REL, "# synthetic entrypoint; never executed\n")
    write(repo / CONTEXT_REL, "# synthetic entrypoint; never executed\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "fixture profile")
    return repo


@pytest.fixture(autouse=True)
def no_host_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-host-config"))
    monkeypatch.delenv("AEGIS_INVOKING_AGENT", raising=False)


def event(repo: Path, command: str, **extra: object) -> str:
    return json.dumps(
        {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(repo),
            "session_id": "synthetic",
            "permission_mode": "dontAsk",
            **extra,
        }
    )


def assert_approval(result: object, kind: str) -> None:
    assert result.returncode == 0, result.stderr
    approval = json.loads(result.stdout)["hookSpecificOutput"]
    assert approval["hookEventName"] == "PreToolUse"
    assert approval["permissionDecision"] == "allow"
    assert approval["permissionDecisionReason"] == f"aegis-orchestrator:{kind}"


@pytest.mark.parametrize("kind", ["project-context", "beads-read", "workflow-begin"])
def test_strict_gate_emits_bounded_native_approval(tmp_path: Path, kind: str) -> None:
    repo = managed_repo(tmp_path)
    command = {
        "project-context": f"python3 {repo / CONTEXT_REL} --root {repo} --check",
        "beads-read": ENV + SCOPED + " show ga-e0t1 --json",
        "workflow-begin": f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-e0t1",
    }[kind]
    assert_approval(run_gate(PRETOOLUSE, repo, event(repo, command)), kind)
    records = (repo / ".aegis/reports/gate-decisions.jsonl").read_text()
    assert f"native_permission:{kind}" in records
    assert command not in records


def test_no_opt_in_leaves_native_permissions_unchanged(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)
    result = run_gate(PRETOOLUSE, repo, event(repo, SCOPED + " ready"))
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("ready", [False, True])
@pytest.mark.parametrize(
    "command",
    [
        "python3 -c 'print(1)'",
        "git status --short",
        "sha256sum README.md",
        "/home/loucmane/gascity/bin/bd show ga-e0t1 --json",
        SCOPED.replace("--rig gascity", "--rig hpfetcher") + " list",
        SCOPED + " update ga-e0t1 --status closed",
        SCOPED + " list --profile",
        SCOPED + " list && touch forbidden",
        SCOPED + " list > output.json",
        "PYTHONPATH=/tmp " + SCOPED + " list",
        SCOPED.replace("gc --city", "gc --city /tmp/other --city") + " list",
        f"python3 {WORKFLOW} begin --root /tmp/other --bead ga-e0t1",
        f"python3 {WORKFLOW} begin --root . --bead ga-e0t1 --force",
        f"python3 {WORKFLOW} begin --root . --bead ga-e0t1 --bead ga-other",
        "/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city rig resume gascity",
    ],
)
def test_profile_never_approves_unrecognized_or_out_of_scope_commands(
    tmp_path: Path,
    ready: bool,
    command: str,
) -> None:
    repo = managed_repo(tmp_path, ready=ready)
    result = run_gate(PRETOOLUSE, repo, event(repo, command))
    assert '"permissionDecision": "allow"' not in result.stdout


@pytest.mark.parametrize("mode", ["observation", "pending", "advisory"])
def test_existing_gate_constraints_still_precede_native_bootstrap_approval(
    tmp_path: Path,
    mode: str,
) -> None:
    repo = managed_repo(tmp_path, ready=True)
    if mode == "observation":
        write(
            repo / ".aegis/state/current-work.json",
            json.dumps(
                {
                    "kind": "observation",
                    "status": "in-progress",
                    "mode": "observation",
                }
            ),
        )
    elif mode == "pending":
        write(
            repo / ".aegis/state/pending-tracking.json",
            json.dumps(
                {
                    "events": [{"id": "pending-1", "status": "pending", "required": True}],
                }
            ),
        )
    else:
        write(repo / ".aegis/state/enforcement.json", '{"mode":"advisory"}')
    command = f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-e0t1"
    result = run_gate(PRETOOLUSE, repo, event(repo, command))
    assert '"permissionDecision": "allow"' not in result.stdout


@pytest.mark.parametrize(
    "defect", ["uncommitted", "wrong-rig", "wrong-root", "unknown", "duplicate", "symlink"]
)
def test_invalid_or_unreviewed_profile_cannot_issue_approval(tmp_path: Path, defect: str) -> None:
    repo = managed_repo(tmp_path)
    value = profile(repo)
    if defect == "wrong-rig":
        value["rig"] = "hpfetcher"
    elif defect == "wrong-root":
        value["canonical_root"] = "/tmp/other"
    elif defect == "unknown":
        value["commands"] = ["all"]
    elif defect == "uncommitted":
        value["commands"] = ["project-context"]
    write(repo / PROFILE, json.dumps(value))
    if defect == "duplicate":
        write(
            repo / PROFILE,
            (repo / PROFILE)
            .read_text()
            .replace(
                '"rig": "gascity"',
                '"rig": "gascity", "rig": "gascity"',
            ),
        )
    if defect == "symlink":
        original = repo / "profile-real.json"
        (repo / PROFILE).rename(original)
        (repo / PROFILE).symlink_to(original)
    if defect != "uncommitted":
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "invalid fixture")
    result = run_gate(PRETOOLUSE, repo, event(repo, SCOPED + " ready"))
    assert result.returncode == 2, result.stderr
    assert '"permissionDecision": "allow"' not in result.stdout


def test_payload_cwd_must_match_governed_root(tmp_path: Path) -> None:
    repo = managed_repo(tmp_path)
    result = run_gate(PRETOOLUSE, repo, event(repo, SCOPED + " ready", cwd="/tmp/other"))
    assert '"permissionDecision": "allow"' not in result.stdout


def test_profile_is_not_a_file_write_or_delegation_grant(tmp_path: Path) -> None:
    repo = managed_repo(tmp_path)
    for name, args in [
        ("Write", {"file_path": "plans/new.md", "content": "not allowed"}),
        ("Write", {"file_path": str(PROFILE), "content": "{}"}),
        ("Agent", {"description": "work", "prompt": "do it", "subagent_type": "worker"}),
    ]:
        result = run_gate(PRETOOLUSE, repo, json.dumps({"tool_name": name, "tool_input": args}))
        assert result.returncode == 2, result.stderr
        assert '"permissionDecision": "allow"' not in result.stdout


@pytest.mark.parametrize("mode", ["plan", "unknown", None])
def test_bootstrap_is_not_approved_in_plan_or_unknown_mode(
    tmp_path: Path, mode: str | None
) -> None:
    repo = managed_repo(tmp_path)
    command = f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-e0t1"
    result = run_gate(PRETOOLUSE, repo, event(repo, command, permission_mode=mode))
    assert '"permissionDecision": "allow"' not in result.stdout


@pytest.mark.parametrize("mode", ["default", "manual", "dontAsk", "acceptEdits", "auto"])
def test_known_native_modes_keep_the_same_bounded_bootstrap_contract(
    tmp_path: Path, mode: str
) -> None:
    repo = managed_repo(tmp_path)
    command = f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-e0t1"
    assert_approval(
        run_gate(PRETOOLUSE, repo, event(repo, command, permission_mode=mode)), "workflow-begin"
    )


def test_profile_can_enable_reads_without_bootstrap(tmp_path: Path) -> None:
    repo = managed_repo(tmp_path)
    data = profile(repo)
    data["commands"] = ["beads-read"]
    write(repo / PROFILE, json.dumps(data))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "read-only fixture")
    assert_approval(run_gate(PRETOOLUSE, repo, event(repo, SCOPED + " ready")), "beads-read")
    command = f"python3 {repo / WORKFLOW_REL} begin --root {repo} --bead ga-e0t1"
    assert (
        '"permissionDecision": "allow"'
        not in run_gate(PRETOOLUSE, repo, event(repo, command)).stdout
    )


@pytest.mark.parametrize("dirty", ["entrypoint", "import", "untracked"])
def test_native_approval_does_not_bless_unreviewed_runtime(tmp_path: Path, dirty: str) -> None:
    repo = managed_repo(tmp_path)
    if dirty == "entrypoint":
        write(repo / CONTEXT_REL, "# modified\n")
    else:
        target = repo / CONTEXT_REL.parent / "project_dependency.py"
        write(target, "# original\n")
        if dirty == "import":
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "fixture module")
            write(target, "# changed\n")
    command = f"python3 {repo / CONTEXT_REL} --root {repo} --check"
    result = run_gate(PRETOOLUSE, repo, event(repo, command))
    assert result.returncode == 2
    assert '"permissionDecision": "allow"' not in result.stdout


def test_linked_worktree_inherits_only_canonical_unchanged_policy(tmp_path: Path) -> None:
    repo = managed_repo(tmp_path)
    lane = repo.parent / (repo.name + "-worktrees") / "ga-lane"
    git(repo, "worktree", "add", "-qb", "codex/ga-lane", str(lane))
    assert_approval(run_gate(PRETOOLUSE, lane, event(lane, SCOPED + " ready")), "beads-read")
    command = f"python3 {repo / CONTEXT_REL} --root {lane} --check"
    # The canonical fixture is not the hook's real runtime, so only the shared
    # grammar (not its source-root allowlist) is patched in the direct unit test.
    from aegis_foundation.gate.hooks import native_permissions
    from unittest.mock import patch
    from aegis_foundation.gate.hooks.contracts import Payload

    with (
        patch.object(native_permissions, "read_only_context", return_value=True),
        patch(
            "aegis_foundation.gate.hooks.native_permissions.hook_invoking_agent",
            return_value="claude",
        ),
    ):
        assert (
            native_permissions.native_permission(
                lane, Payload("Bash", {"command": command}, cwd=str(lane))
            )
            == "project-context"
        )
    value = profile(repo)
    value["commands"] = ["beads-read"]
    write(lane / PROFILE, json.dumps(value))
    git(lane, "add", ".")
    git(lane, "commit", "-qm", "task must not change canonical approval")
    result = run_gate(PRETOOLUSE, lane, event(lane, SCOPED + " ready"))
    assert result.returncode == 2
    assert '"permissionDecision": "allow"' not in result.stdout


def test_audit_failure_denies_before_native_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from aegis_foundation.gate.hooks import decisions, native_permissions
    from aegis_foundation.gate.hooks.contracts import Payload

    repo = managed_repo(tmp_path)
    monkeypatch.setattr(native_permissions, "native_permission", lambda *args: "beads-read")

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("audit unavailable")

    monkeypatch.setattr(decisions, "append_gate_decision", fail)
    assert (
        decisions.gate_allow_or_record(
            repo, Payload("Bash", {"command": SCOPED + " ready"}), reason="read_only"
        )
        == 2
    )
    assert capsys.readouterr().out == ""


def test_real_context_entrypoint_size_is_not_a_profile_size_limit(tmp_path: Path) -> None:
    repo = managed_repo(tmp_path)
    write(repo / CONTEXT_REL, CONTEXT.read_text())
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "real entrypoint bytes; never executed")
    command = f"python3 {repo / CONTEXT_REL} --root {repo} --check"
    assert_approval(run_gate(PRETOOLUSE, repo, event(repo, command)), "project-context")


def test_profile_failure_does_not_intercept_unrelated_existing_read_permissions(
    tmp_path: Path,
) -> None:
    repo = managed_repo(tmp_path)
    write(repo / PROFILE, "not JSON")
    result = run_gate(PRETOOLUSE, repo, event(repo, "git status --short"))
    assert result.returncode == 0
    assert result.stdout == ""
