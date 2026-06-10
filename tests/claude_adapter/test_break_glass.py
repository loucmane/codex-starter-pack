"""TM #201: break-glass recovery contract.

Every BLOCKED state carries a copyable safe repair + blast-radius tier + audit
destination + escalation; `aegis override` mints a one-shot, rate-limited token honored
ONLY for workflow-state (tier a/b) blocks and consumed on use. It is never a generic
bypass: tier-c blocks (observation boundary, protected paths, adversarial) ignore it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"

sys.path.insert(0, str(REPO_ROOT))


def load_gate_lib():
    spec = importlib.util.spec_from_file_location("gate_lib_breakglass", GATE_LIB)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gate_lib_breakglass"] = module
    spec.loader.exec_module(module)
    return module


gate_lib = load_gate_lib()


def make_blocked_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    subprocess.run(["git", "checkout", "-q", "-b", "main"], cwd=repo, check=False)  # no task id => BLOCKED
    return repo


def run_pretooluse(repo: Path, payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "pretooluse"],
        cwd=repo,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def mint_override(repo: Path, reason_class: str = "any", state_home: Path | None = None) -> dict:
    env = dict(os.environ)
    if state_home is not None:
        env["XDG_STATE_HOME"] = state_home.as_posix()
    result = subprocess.run(
        [
            sys.executable, "-m", "aegis_foundation.cli", "override",
            "--reason", "deadlock recovery", "--reason-class", reason_class,
            "--target-dir", repo.as_posix(),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_recovery_contract_covers_block_reasons() -> None:
    for reason in ("readiness_blocked", "pending_tracking", "observation_mode_disallowed_mutation"):
        contract = gate_lib.recovery_contract(reason)
        assert contract["repair"]
        assert contract["tier"] in {"a", "b", "c"}
        assert contract["audit"]
        assert contract["escalation"]
    assert gate_lib.recovery_contract("readiness_blocked")["override_eligible"] == "true"
    assert gate_lib.recovery_contract("observation_mode_disallowed_mutation")["override_eligible"] == "false"
    assert gate_lib.recovery_contract("unknown_reason")["override_eligible"] == "false"


def test_blocked_message_carries_recovery_contract(tmp_path: Path) -> None:
    repo = make_blocked_repo(tmp_path)
    result = run_pretooluse(repo, {"tool_name": "Bash", "tool_input": {"command": "touch x"}})
    assert result.returncode == 2
    assert "Aegis recovery contract" in result.stderr
    assert "blast-radius tier:" in result.stderr
    assert "copyable safe repair:" in result.stderr
    assert "aegis override --reason" in result.stderr


def test_override_token_unblocks_one_workflow_state_mutation(tmp_path: Path) -> None:
    repo = make_blocked_repo(tmp_path)
    blocked = run_pretooluse(repo, {"tool_name": "Bash", "tool_input": {"command": "touch x"}})
    assert blocked.returncode == 2
    mint_override(repo, "readiness_blocked")
    first = run_pretooluse(repo, {"tool_name": "Bash", "tool_input": {"command": "touch x"}})
    assert first.returncode == 0, first.stderr
    assert "BREAK-GLASS" in first.stderr
    # Single use: the very next mutation is blocked again.
    second = run_pretooluse(repo, {"tool_name": "Bash", "tool_input": {"command": "touch y"}})
    assert second.returncode == 2
    assert not (repo / ".aegis" / "state" / "override-token.json").exists()


def test_override_records_audit_event(tmp_path: Path) -> None:
    repo = make_blocked_repo(tmp_path)
    state_home = tmp_path / "state"
    mint_override(repo, "readiness_blocked")
    run_pretooluse(repo, {"tool_name": "Bash", "tool_input": {"command": "touch x"}}, {"XDG_STATE_HOME": state_home.as_posix()})
    ledger_lib_spec = importlib.util.spec_from_file_location(
        "ledger_for_breakglass", REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"
    )
    ledger_lib = importlib.util.module_from_spec(ledger_lib_spec)
    ledger_lib_spec.loader.exec_module(ledger_lib)
    ledger = ledger_lib.open_ledger(cwd=repo, env={"XDG_STATE_HOME": state_home.as_posix()})
    try:
        overrides = ledger.read(event_type="override")
    finally:
        ledger.close()
    assert len(overrides) == 1
    assert overrides[0]["extra"]["reason_class"] == "readiness_blocked"
    assert overrides[0]["extra"]["note"] == "deadlock recovery"


def test_override_never_bypasses_observation_boundary(tmp_path: Path) -> None:
    repo = tmp_path / "obs"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/task-9-x"], cwd=repo, check=False)
    state = repo / ".aegis" / "state"
    state.mkdir(parents=True)
    (state / "current-work.json").write_text(
        json.dumps(
            {
                "schema_version": "1",
                "status": "in-progress",
                "mode": "observation",
                "task": {"id": "9", "slug": "x", "status": "in-progress"},
            }
        ),
        encoding="utf-8",
    )
    mint_override(repo, "any")
    # Source edit during observation is a tier-c boundary block — override must NOT clear it.
    result = run_pretooluse(repo, {"tool_name": "Edit", "tool_input": {"file_path": "src/x.ts", "old_string": "a", "new_string": "b"}})
    assert result.returncode == 2
    assert "observation mode only permits observation tooling" in result.stderr
    # The token is untouched (only eligible reasons consume it).
    assert (repo / ".aegis" / "state" / "override-token.json").exists()


def test_override_reason_class_scoping(tmp_path: Path) -> None:
    repo = make_blocked_repo(tmp_path)
    # A pending_tracking-scoped token must not clear a readiness_blocked block.
    mint_override(repo, "pending_tracking")
    result = run_pretooluse(repo, {"tool_name": "Bash", "tool_input": {"command": "touch x"}})
    assert result.returncode == 2, "scoped token must not apply to a different reason class"
    assert (repo / ".aegis" / "state" / "override-token.json").exists()


def test_override_rate_limited(tmp_path: Path) -> None:
    repo = make_blocked_repo(tmp_path)
    for _ in range(3):
        result = subprocess.run(
            [sys.executable, "-m", "aegis_foundation.cli", "override", "--reason", "r", "--max-per-day", "3", "--target-dir", repo.as_posix()],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0
    over = subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "override", "--reason", "r", "--max-per-day", "3", "--target-dir", repo.as_posix()],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert over.returncode == 1
    assert "rate limit" in over.stderr


def test_override_command_runs_while_blocked(tmp_path: Path) -> None:
    repo = make_blocked_repo(tmp_path)
    result = run_pretooluse(
        repo,
        {"tool_name": "Bash", "tool_input": {"command": "python3 -m aegis_foundation.cli override --reason x"}},
    )
    assert result.returncode == 0, "minting a token must itself be allowed while BLOCKED"


def test_gate_classifies_override_payload() -> None:
    assert gate_lib.payload_is_aegis_override(
        gate_lib.Payload("Bash", {"command": "python3 -m aegis_foundation.cli override --reason x"})
    ) is True
    assert gate_lib.payload_is_aegis_override(gate_lib.Payload("Bash", {"command": "git status"})) is False


def test_assets_and_live_gate_lib_identical() -> None:
    live = (REPO_ROOT / ".claude" / "scripts" / "gate_lib.py").read_bytes()
    asset = (REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "gate_lib.py").read_bytes()
    assert live == asset
