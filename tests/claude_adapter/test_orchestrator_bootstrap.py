"""ga-e0t1: transcript regressions and the pre-kickoff authorization boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_foundation.gate.hooks import decisions, payloads, shell_policy
from aegis_foundation.gate.hooks.contracts import Payload
from aegis_foundation.gate.hooks.tracking import match_gate_command
from test_pretooluse_gates import PRETOOLUSE, REPO_ROOT, make_repo, payload, run_gate

GC = "/home/loucmane/gascity/bin/gc"
BD = "/home/loucmane/gascity/bin/bd"
CITY = "/home/loucmane/gascity/city"
HOME = "/home/loucmane/gascity/home"
PATH = "/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin"
SCOPED = f"{GC} --city {CITY} --rig gascity bd"
WORKFLOW = REPO_ROOT / "plugins/gas-city-workflow/scripts/workflow.py"
CONTEXT = REPO_ROOT / "plugins/gas-city-workflow/scripts/project_context.py"


@pytest.mark.parametrize(
    "command",
    [
        f"{BD} show ga-e0t1",
        f"{BD} show ga-ur1c.5.1.7 --json --readonly",
        f"{BD} ready --json",
        f"{SCOPED} list --all --limit 0 --json --readonly",
        f"{SCOPED} ready",
        f"GC_HOME={HOME} {SCOPED} show ga-e0t1 --json",
        f"env PATH={PATH} GC_HOME={HOME} {SCOPED} list",
        f"/usr/bin/env PATH={PATH} GC_HOME={HOME} {SCOPED} list",
        f"/usr/bin/env -u BEADS_DIR -u BEADS_DB PATH={PATH} GC_HOME={HOME} {SCOPED} list",
        f"/usr/bin/env PATH={PATH} git status --short",
        "sha256sum README.md",
        "readlink sessions/current",
    ],
)
def test_transcript_reads_pass_while_readiness_is_blocked(tmp_path: Path, command: str) -> None:
    repo = make_repo(tmp_path, ready=False)
    result = run_gate(PRETOOLUSE, repo, payload("Bash", command=command))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        f"{SCOPED} list --profile",  # bd's CPU profiler writes a file.
        f"{SCOPED} show ga-e0t1 --db /tmp/other",
        f"{SCOPED} list --global",
        f"{SCOPED} list --watch",
        f"{SCOPED} list --json=false",
        f"{SCOPED} show ga-e0t1 --unknown",
        f"{GC} --city /tmp/other --rig gascity bd list",
        f"{GC} bd list",
        f"{BD} update ga-e0t1 --status closed",
        f"{BD} create new-task",
        f"{BD} close ga-e0t1",
        f"{BD} dep add ga-e0t1 ga-other",
        f"{GC} --city {CITY} rig resume gascity",
        f"{GC} --city {CITY} sling gascity/implementation-worker ga-e0t1",
        f"{SCOPED} show ga-e0t1 > output.json",
        f"{SCOPED} list && touch forbidden",
        f"{SCOPED} list\n{BD} update ga-e0t1 --status closed",
        f"GC_HOME=$(pwd) {SCOPED} list",
        f"GC_HOME=$HOME {SCOPED} list",
        f"PATH=/tmp/bin {SCOPED} list",
        "env GIT_PAGER=evil git log",
        f"/usr/bin/env LD_PRELOAD=/tmp/evil.so {SCOPED} list",
        f"PYTHONPATH=/tmp/evil {SCOPED} list",
        "PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/foo.py",
        f"/usr/bin/env -u PATH {SCOPED} list",
        f"/usr/bin/env -C /tmp {SCOPED} list",
        f"GC_HOME={HOME}",
        f"env -S 'PATH={PATH} {SCOPED} list'",
        f"/tmp/env PATH={PATH} {SCOPED} list",
        "python3 -c 'print(1)'",
        "uniq input output",
        "/tmp/readlink sessions/current",
        "/tmp/sha256sum README.md",
    ],
)
def test_unsafe_or_unclassified_commands_remain_blocked(tmp_path: Path, command: str) -> None:
    repo = make_repo(tmp_path, ready=False)
    result = run_gate(PRETOOLUSE, repo, payload("Bash", command=command))
    assert result.returncode == 2, (command, result.stderr)


def test_lookalike_managed_binary_is_not_trusted(tmp_path: Path) -> None:
    fake = tmp_path / "bd"
    fake.symlink_to(BD)
    assert not shell_policy.bash_is_read_only(f"{fake} list --json")


def test_literal_path_controls_bare_binary_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    def which(name: str, path: str | None = None) -> str:
        assert path == PATH
        return BD if name == "bd" else "/usr/bin/env"

    monkeypatch.setattr(payloads.shutil, "which", which)
    assert payloads.strip_shell_prefixes([f"PATH={PATH}", "bd", "list"]) == [BD, "list"]


def test_post_execution_label_is_not_execution_authority() -> None:
    command = "PYTHONDONTWRITEBYTECODE=1 pnpm -C app typecheck"
    assert match_gate_command(command, {"app": {"typecheck": ["pnpm -C app typecheck"]}}) == (
        "app",
        "typecheck",
    )
    assert not shell_policy.bash_is_read_only(command)


def test_context_inspection_pins_script_target_and_flags(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)
    command = f"python3 {CONTEXT} --root {repo} --check"
    assert run_gate(PRETOOLUSE, repo, payload("Bash", command=command)).returncode == 0
    for extra in (" --registry /tmp/registry.json", " --output /tmp/output"):
        assert run_gate(PRETOOLUSE, repo, payload("Bash", command=command + extra)).returncode == 2
    elsewhere = f"python3 {CONTEXT} --root /tmp/other --check"
    assert run_gate(PRETOOLUSE, repo, payload("Bash", command=elsewhere)).returncode == 2


@pytest.mark.parametrize("kind", ["workflow", "wizard"])
def test_exact_bootstrap_is_mutation_but_reachable_when_blocked(tmp_path: Path, kind: str) -> None:
    repo = make_repo(tmp_path, ready=False)
    if kind == "workflow":
        command = f"python3 {WORKFLOW} begin --root {repo} --bead ga-e0t1 --goal repair"
    else:
        command = (
            f"python3 {REPO_ROOT}/scripts/codex-task wizard kickoff "
            f"--bead ga-e0t1 --slug repair --title Repair --target-dir {repo}"
        )
    assert not shell_policy.bash_is_read_only(command)
    result = run_gate(PRETOOLUSE, repo, payload("Bash", command=command))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "suffix",
    [
        " --registry /tmp/registry.json",
        " --force",
        " --root /tmp/other",
        " --bead ga-other",
        " && touch forbidden",
        " > output.json",
    ],
)
def test_bootstrap_is_not_an_arbitrary_escape(tmp_path: Path, suffix: str) -> None:
    repo = make_repo(tmp_path, ready=False)
    command = f"python3 {WORKFLOW} begin --root {repo} --bead ga-e0t1{suffix}"
    assert run_gate(PRETOOLUSE, repo, payload("Bash", command=command)).returncode == 2


def test_bootstrap_rejects_environment_injection_and_lookalike_script(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)
    command = f"python3 {WORKFLOW} begin --root {repo} --bead ga-e0t1"
    assert (
        run_gate(PRETOOLUSE, repo, payload("Bash", command=f"PYTHONPATH=/tmp {command}")).returncode
        == 2
    )
    fake = tmp_path / "workflow.py"
    fake.symlink_to(WORKFLOW)
    assert (
        run_gate(
            PRETOOLUSE, repo, payload("Bash", command=command.replace(str(WORKFLOW), str(fake)))
        ).returncode
        == 2
    )


def test_shared_wizard_cannot_default_to_another_source_root(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)
    command = (
        f"python3 {REPO_ROOT}/scripts/codex-task wizard kickoff "
        "--bead ga-e0t1 --slug repair --title Repair"
    )
    assert run_gate(PRETOOLUSE, repo, payload("Bash", command=command)).returncode == 2


@pytest.mark.parametrize("suffix", [" --force", " --task 103", " --handler-target /tmp/other"])
def test_wizard_cannot_weaken_its_internal_guards(tmp_path: Path, suffix: str) -> None:
    repo = make_repo(tmp_path, ready=False)
    command = (
        f"python3 {REPO_ROOT}/scripts/codex-task wizard kickoff "
        f"--bead ga-e0t1 --slug repair --title Repair --target-dir {repo}{suffix}"
    )
    assert run_gate(PRETOOLUSE, repo, payload("Bash", command=command)).returncode == 2


def test_strict_denial_is_audited_without_raw_input(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ready=False)
    marker = "do-not-copy-private-content"
    result = run_gate(PRETOOLUSE, repo, payload("Write", file_path="README.md", content=marker))
    assert result.returncode == 2
    log = (repo / ".aegis/reports/gate-decisions.jsonl").read_text()
    record = json.loads(log.splitlines()[-1])
    assert record["verdict"] == "block"
    assert record["reason"] == "readiness_blocked"
    assert record["mode"] == "strict"
    assert len(record["payload_digest"]) == 64
    assert marker not in log


def test_audit_failure_cannot_change_strict_denial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise OSError("ledger unavailable")

    monkeypatch.setattr(decisions, "append_gate_decision", broken)
    assert (
        decisions.gate_block_or_record(
            tmp_path,
            Payload("Write", {"file_path": "README.md"}),
            "denied",
            reason="readiness_blocked",
        )
        == 2
    )
