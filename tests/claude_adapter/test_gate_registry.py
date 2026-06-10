"""PR-1d tests: gate registry matching, verification classification, seed-once
brief.json, and scope records (spec sections 2 and 2.1).

The merge gate for this slice is the fixture suite covering cd-prefix, `-C`, and
`--dir` invocation variants of the same logical command.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"

sys.path.insert(0, str(REPO_ROOT))
from scripts import _aegis_installer  # noqa: E402


def load_gate_lib():
    spec = importlib.util.spec_from_file_location("gate_lib_registry_tests", GATE_LIB)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["gate_lib_registry_tests"] = module
    spec.loader.exec_module(module)
    return module


gate_lib = load_gate_lib()

GATES = {
    "app": {
        "typecheck": [
            "cd app && pnpm typecheck",
            "pnpm -C app typecheck",
            "pnpm --dir app typecheck",
        ],
        "test": ["cd app && pnpm test", "pnpm -C app test"],
    },
    "worker": {"lint": ["cd worker && pnpm lint", "pnpm -C worker lint"]},
}


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("cd app && pnpm typecheck", ("app", "typecheck")),
        ("pnpm -C app typecheck", ("app", "typecheck")),
        ("pnpm --dir app typecheck", ("app", "typecheck")),
        ("cd app && pnpm typecheck 2>&1 | tail -20", ("app", "typecheck")),
        ("PYTHONDONTWRITEBYTECODE=1 pnpm -C app typecheck", ("app", "typecheck")),
        ("pnpm -C worker lint", ("worker", "lint")),
        ("cd worker && pnpm lint > /tmp/out.txt 2>&1", ("worker", "lint")),
        ("echo before && cd app && pnpm test", ("app", "test")),
    ],
)
def test_gate_matching_handles_invocation_variants(command: str, expected: tuple[str, str]) -> None:
    assert gate_lib.match_gate_command(command, GATES) == expected


@pytest.mark.parametrize(
    "command",
    [
        "pnpm typecheck",
        "pnpm -C app typecheck --watch",
        "cd app && pnpm build",
        "pnpm -C parser test",
        "echo pnpm -C app typecheck",
        "",
    ],
)
def test_gate_matching_rejects_non_matches(command: str) -> None:
    assert gate_lib.match_gate_command(command, GATES) is None


def test_gate_matching_empty_registry() -> None:
    assert gate_lib.match_gate_command("cd app && pnpm typecheck", {}) is None


def make_repo(tmp_path: Path, branch: str = "feat/task-77-sample") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    assert subprocess.run(["git", "init", "-q"], cwd=repo, check=False).returncode == 0
    assert subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=repo, check=False).returncode == 0
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=False,
    )
    return repo


def write_brief(repo: Path, **overrides: object) -> None:
    brief = {
        "gates": GATES,
        "source_roots": ["app/", "worker/"],
        "thresholds": {"branch_count": 30, "unignored_file_mb": 5},
        "redact_extra": [],
        "archive_keep": 20,
        "inject": True,
    }
    brief.update(overrides)
    path = repo / ".aegis" / "brief.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief), encoding="utf-8")


def run_record(repo: Path, state_home: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state_home.as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    return subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "record"],
        cwd=repo,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def read_events(state_home: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for db in (state_home / "aegis").glob("*/ledger.db"):
        connection = sqlite3.connect(db.as_posix())
        for row in connection.execute(
            "SELECT event_type, branch, outcome, extra FROM events ORDER BY seq"
        ):
            events.append(
                {"event_type": row[0], "branch": row[1], "outcome": row[2], "extra": json.loads(row[3])}
            )
        connection.close()
    return events


def bash_payload(repo: Path, command: str, hook_event: str = "PostToolUse") -> dict[str, object]:
    return {
        "session_id": "sess-registry",
        "cwd": repo.as_posix(),
        "hook_event_name": hook_event,
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {"stdout": "", "stderr": "", "interrupted": False},
        "duration_ms": 10,
    }


def test_recorder_classifies_verification_with_commit(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_brief(repo)
    state = tmp_path / "state"
    assert run_record(repo, state, bash_payload(repo, "cd app && pnpm typecheck 2>&1 | tail -5")).returncode == 0
    verifications = [event for event in read_events(state) if event["event_type"] == "verification"]
    assert len(verifications) == 1
    extra = verifications[0]["extra"]
    assert extra["package"] == "app" and extra["gate"] == "typecheck"
    assert verifications[0]["outcome"] == "pass"
    assert isinstance(extra.get("commit"), str) and len(extra["commit"]) >= 7


def test_recorder_verification_failure_maps_exit_class(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_brief(repo)
    state = tmp_path / "state"
    payload = bash_payload(repo, "pnpm -C worker lint", hook_event="PostToolUseFailure")
    payload["error"] = "lint failed"
    assert run_record(repo, state, payload).returncode == 0
    verification = [event for event in read_events(state) if event["event_type"] == "verification"][0]
    assert verification["outcome"] == "fail"
    assert verification["extra"]["gate"] == "lint"


def test_recorder_honors_redact_extra_from_brief(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_brief(repo, redact_extra=["hp-secret-[0-9]+"])
    state = tmp_path / "state"
    assert run_record(repo, state, bash_payload(repo, "echo deploy hp-secret-999 now")).returncode == 0
    events = read_events(state)
    assert "hp-secret-999" not in json.dumps(events)


def test_scope_record_inferred_once_per_branch(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, branch="feat/task-77-sample")
    write_brief(repo)
    state = tmp_path / "state"
    mutation = bash_payload(repo, "touch app/x.ts")
    assert run_record(repo, state, mutation).returncode == 0
    assert run_record(repo, state, mutation).returncode == 0
    scopes = [event for event in read_events(state) if event["event_type"] == "scope"]
    assert len(scopes) == 1
    extra = scopes[0]["extra"]
    assert extra["task_id"] == "77"
    assert extra["inferred"] is True
    assert extra["needs_confirmation"] is False
    assert extra["path_globs"] == ["app/", "worker/"]
    assert "app:typecheck" in extra["gates"]


def test_scope_record_ambiguous_branch_needs_confirmation(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, branch="experiment/no-id")
    write_brief(repo)
    state = tmp_path / "state"
    assert run_record(repo, state, bash_payload(repo, "touch app/x.ts")).returncode == 0
    scopes = [event for event in read_events(state) if event["event_type"] == "scope"]
    assert len(scopes) == 1
    assert scopes[0]["extra"]["task_id"] is None
    assert scopes[0]["extra"]["needs_confirmation"] is True


def test_read_only_commands_do_not_create_scope_records(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_brief(repo)
    state = tmp_path / "state"
    assert run_record(repo, state, bash_payload(repo, "git status")).returncode == 0
    assert [event for event in read_events(state) if event["event_type"] == "scope"] == []


def test_scope_set_cli_appends_confirmed_record(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, branch="experiment/no-id")
    state = tmp_path / "state"
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state.as_posix()
    result = subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "scope", "set", "205", "app/", "--target-dir", repo.as_posix()],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    scopes = [event for event in read_events(state) if event["event_type"] == "scope"]
    assert len(scopes) == 1
    assert scopes[0]["extra"] == {
        "task_id": "205",
        "path_globs": ["app/"],
        "inferred": False,
        "confirmed": True,
    }


def test_sync_hook_emits_scope_nudge_once(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, branch="experiment/no-id")
    write_brief(repo)
    state = tmp_path / "state"
    assert run_record(repo, state, bash_payload(repo, "touch app/x.ts")).returncode == 0
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state.as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    payload = json.dumps(
        {
            "session_id": "sess-registry",
            "cwd": repo.as_posix(),
            "tool_name": "Bash",
            "tool_input": {"command": "touch app/y.ts"},
        }
    )
    first = subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "posttooluse"],
        cwd=repo, input=payload, text=True, capture_output=True, env=env, check=False,
    )
    assert first.returncode == 0
    assert "aegis scope set" in first.stdout
    assert "additionalContext" in first.stdout
    second = subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "posttooluse"],
        cwd=repo, input=payload, text=True, capture_output=True, env=env, check=False,
    )
    assert second.returncode == 0
    assert "aegis scope set" not in second.stdout, "nudge must never repeat for a branch"


def test_sync_hook_nudge_suppressed_after_confirmation(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, branch="experiment/no-id")
    write_brief(repo)
    state = tmp_path / "state"
    assert run_record(repo, state, bash_payload(repo, "touch app/x.ts")).returncode == 0
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state.as_posix()
    subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "scope", "set", "205", "--target-dir", repo.as_posix()],
        cwd=REPO_ROOT, capture_output=True, text=True, env=env, check=False,
    )
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    result = subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "posttooluse"],
        cwd=repo,
        input=json.dumps({"cwd": repo.as_posix(), "tool_name": "Bash", "tool_input": {"command": "touch a"}}),
        text=True, capture_output=True, env=env, check=False,
    )
    assert "aegis scope set" not in result.stdout


def test_brief_asset_seeded_once_and_never_clobbered(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert subprocess.run(["git", "init", "-q"], cwd=target, check=False).returncode == 0
    plan = _aegis_installer.plan_install(
        target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"]
    )
    brief_ops = [op for op in plan["operations"] if op["path"] == ".aegis/brief.json"]
    assert brief_ops and brief_ops[0]["classification"] == "create"
    custom = target / ".aegis" / "brief.json"
    custom.parent.mkdir(parents=True, exist_ok=True)
    custom.write_text(json.dumps({"gates": {"app": {"test": ["pnpm test"]}}}), encoding="utf-8")
    replan = _aegis_installer.plan_install(
        target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"]
    )
    brief_ops = [op for op in replan["operations"] if op["path"] == ".aegis/brief.json"]
    assert brief_ops[0]["classification"] == "skip"
    assert "owner-maintained" in brief_ops[0]["reason"]


def test_manifest_accepts_config_kind() -> None:
    assets = _aegis_installer._managed_assets(REPO_ROOT, "claude", ("claude",))
    brief = next(asset for asset in assets if asset.path == ".aegis/brief.json")
    assert brief.kind == "config"
    payload = json.loads(_aegis_installer._render_default_brief().decode("utf-8"))
    assert payload["gates"] == {}
    assert payload["archive_keep"] == 20
