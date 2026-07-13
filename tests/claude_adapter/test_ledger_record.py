"""PR-1b recorder tests: fixture-driven gate_lib `record`, renderer, dispatcher, rider.

Fixtures under tests/fixtures/hook_payloads/ are REAL payloads captured from a live
Claude Code session (spec section 2 payload reality check), including subagent
attribution. The recorder contract: always exit 0, never block, degrade silently.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"
LEDGER_LIB = REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"
BRIEF_LIB = REPO_ROOT / ".claude" / "scripts" / "brief_lib.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "hook_payloads"

sys.path.insert(0, str(REPO_ROOT))
from scripts import _aegis_installer  # noqa: E402
from aegis_foundation import cli  # noqa: E402


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


brief_lib = load_module(BRIEF_LIB, "brief_lib_for_ledger_record_tests")


def load_fixture_lines(name: str) -> list[dict[str, object]]:
    path = FIXTURES / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert subprocess.run(["git", "init", "-q"], cwd=repo, check=False).returncode == 0
    return repo


def run_record(repo: Path, state_home: Path, payload: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state_home.as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    return subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "record"],
        cwd=repo,
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def read_events(state_home: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for db in (state_home / "aegis").glob("*/ledger.db"):
        connection = sqlite3.connect(db.as_posix())
        cursor = connection.execute(
            "SELECT event_type, tool_name, outcome, session_id, agent_id, agent_type, "
            "duration_ms, paths, extra, handler FROM events ORDER BY seq"
        )
        for row in cursor.fetchall():
            events.append(
                {
                    "event_type": row[0],
                    "tool_name": row[1],
                    "outcome": row[2],
                    "session_id": row[3],
                    "agent_id": row[4],
                    "agent_type": row[5],
                    "duration_ms": row[6],
                    "paths": json.loads(row[7]),
                    "extra": json.loads(row[8]),
                    "handler": row[9],
                }
            )
        connection.close()
    return events


def test_recorder_handles_all_captured_posttooluse_fixtures(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    fixtures = load_fixture_lines("PostToolUse")
    assert fixtures, "real PostToolUse fixtures required"
    for fixture in fixtures:
        result = run_record(repo, state, json.dumps(fixture))
        assert result.returncode == 0, result.stderr
    events = [event for event in read_events(state) if event["event_type"] != "scope"]
    assert len(events) == len(fixtures)
    by_tool = {event["tool_name"] for event in events}
    assert {"Bash", "Write", "Edit"} <= by_tool
    for event in events:
        assert event["outcome"] == "pass"
        assert event["session_id"]
        assert event["extra"]["hook_event_name"] == "PostToolUse"
    write_event = next(event for event in events if event["tool_name"] == "Write")
    assert any(path.endswith("sample.txt") for path in write_event["paths"])
    assert isinstance(write_event["duration_ms"], int)


def test_recorder_classifies_failure_fixture(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    fixture = load_fixture_lines("PostToolUseFailure")[0]
    assert run_record(repo, state, json.dumps(fixture)).returncode == 0
    events = read_events(state)
    assert len(events) == 1
    assert events[0]["event_type"] == "tool_failure"
    assert events[0]["outcome"] == "fail"
    assert "does not exist" in str(events[0]["extra"].get("error"))


def test_recorder_keeps_atomic_codex_apply_patch_metadata(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    command = """*** Begin Patch
*** Add File: src/first.py
+first = True
*** Update File: src/old.py
*** Move to: src/new.py
@@
-old
+new
*** End Patch"""
    hook_payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": command},
        "tool_response": {"success": True},
        "session_id": "task248-live",
        "tool_use_id": "apply-patch-1",
        "cwd": repo.as_posix(),
    }

    assert run_record(repo, state, json.dumps(hook_payload)).returncode == 0

    event = next(event for event in read_events(state) if event["tool_name"] == "apply_patch")
    assert event["event_type"] == "mutation"
    assert event["handler"] == "codex:apply_patch"
    assert event["paths"] == ["src/first.py", "src/old.py", "src/new.py"]
    assert event["extra"]["primary_evidence_path"] == "src/first.py"
    assert event["extra"]["affected_paths"] == event["paths"]
    assert [operation["operation"] for operation in event["extra"]["operations"]] == [
        "add",
        "move",
    ]
    assert event["extra"]["operations"][1]["content_operation"] == "update"
    assert event["extra"]["patch_digest"] == sha256(command.encode("utf-8")).hexdigest()


def test_recorder_keeps_subagent_attribution(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    subagent_fixtures = [
        fixture for fixture in load_fixture_lines("PostToolUse") if fixture.get("agent_id")
    ]
    assert subagent_fixtures, "captured fixtures must include a subagent-context event"
    assert run_record(repo, state, json.dumps(subagent_fixtures[0])).returncode == 0
    event = read_events(state)[0]
    assert event["agent_id"] == subagent_fixtures[0]["agent_id"]
    assert event["agent_type"] == subagent_fixtures[0]["agent_type"]


def test_recorder_classifies_delivery_and_task_truth(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    base = load_fixture_lines("PostToolUse")[0]
    delivery = dict(base)
    delivery["tool_input"] = {"command": "git push -u origin feat/task-203-capsule-record-hooks"}
    assert run_record(repo, state, json.dumps(delivery)).returncode == 0
    taskmaster = dict(base)
    taskmaster["tool_input"] = {"command": "task-master set-status --id=203 --status=done"}
    assert run_record(repo, state, json.dumps(taskmaster)).returncode == 0
    tasks_json_edit = dict(base)
    tasks_json_edit["tool_name"] = "Edit"
    tasks_json_edit["tool_input"] = {
        "file_path": (repo / ".taskmaster" / "tasks" / "tasks.json").as_posix(),
        "old_string": "a",
        "new_string": "b",
    }
    assert run_record(repo, state, json.dumps(tasks_json_edit)).returncode == 0
    kinds = [event["event_type"] for event in read_events(state) if event["event_type"] != "scope"]
    assert kinds == ["delivery", "task_truth", "task_truth"]


def test_recorder_refreshes_capsule_for_boundary_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    monkeypatch.setenv("XDG_STATE_HOME", state.as_posix())
    base = load_fixture_lines("PostToolUse")[0]

    cases = (
        ({"tool_name": "Bash", "tool_input": {"command": "task-master set-status --id=227 --status=done"}}, "task-status-change"),
        ({"tool_name": "Bash", "tool_input": {"command": "aegis witness --target-dir ."}}, "pre-delivery"),
        ({"tool_name": "Bash", "tool_input": {"command": "aegis verify --target-dir . --strict"}}, "verification"),
        ({"tool_name": "Bash", "tool_input": {"command": "gh pr merge 244 --squash --delete-branch"}}, "post-merge"),
        (
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": (repo / ".aegis" / "capsule" / "risk-seed.json").as_posix(),
                    "content": "[]",
                },
            },
            "risk-register-change",
        ),
    )

    for update, expected_reason in cases:
        payload = dict(base)
        payload.update(update)
        assert run_record(repo, state, json.dumps(payload)).returncode == 0
        capsule = json.loads((repo / ".aegis" / "capsule" / "current.json").read_text(encoding="utf-8"))
        assert capsule["capsule_meta"]["compile_reason"] == expected_reason
        assert brief_lib.capsule_status(repo)["status"] == "fresh"


def test_recorder_records_session_boundaries(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    start = load_fixture_lines("SessionStart")[0]
    end = load_fixture_lines("SessionEnd")[0]
    assert run_record(repo, state, json.dumps(start)).returncode == 0
    assert run_record(repo, state, json.dumps(end)).returncode == 0
    kinds = [event["event_type"] for event in read_events(state)]
    assert kinds == ["session_begin", "session_end"]


def test_recorder_never_fails_on_garbage_or_missing_store(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    assert run_record(repo, state, "not-json{{{").returncode == 0
    assert run_record(repo, state, "").returncode == 0
    assert run_record(repo, state, json.dumps({"hook_event_name": "PostToolUse"})).returncode == 0
    plain_dir = tmp_path / "no-git"
    plain_dir.mkdir()
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state.as_posix()
    env["CLAUDE_PROJECT_DIR"] = plain_dir.as_posix()
    result = subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "record"],
        cwd=plain_dir,
        input=json.dumps(load_fixture_lines("PostToolUse")[0]),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0


def test_recorder_exits_zero_without_ledger_lib(tmp_path: Path) -> None:
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    (isolated / "gate_lib.py").write_text(GATE_LIB.read_text(encoding="utf-8"), encoding="utf-8")
    repo = make_repo(tmp_path)
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    result = subprocess.run(
        [sys.executable, (isolated / "gate_lib.py").as_posix(), "record"],
        cwd=repo,
        input=json.dumps(load_fixture_lines("PostToolUse")[0]),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0


def test_recorder_redacts_secret_command_text(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    base = load_fixture_lines("PostToolUse")[0]
    secret = dict(base)
    secret["tool_input"] = {"command": "curl -H 'Authorization: Bearer topsecret-token-value'"}
    assert run_record(repo, state, json.dumps(secret)).returncode == 0
    event = read_events(state)[0]
    assert "topsecret-token-value" not in json.dumps(event["extra"])


def test_settings_renderer_adds_async_record_hooks() -> None:
    settings = json.loads(_aegis_installer._render_claude_settings().decode("utf-8"))
    post = settings["hooks"]["PostToolUse"]
    assert post[0]["hooks"][0]["command"].endswith("posttooluse-tracking.sh")
    record = post[1]["hooks"][0]
    # Shell-form on purpose: live probe showed $CLAUDE_PROJECT_DIR is not expanded in
    # exec-form args on CLI 2.1.170; async is the load-bearing property.
    assert record["command"] == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/ledger-record.sh"
    assert "args" not in record
    assert record["async"] is True
    failure = settings["hooks"]["PostToolUseFailure"][0]["hooks"][0]
    assert failure["command"] == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/ledger-record.sh"
    assert failure["async"] is True


def test_live_settings_register_record_hooks() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    post_commands = json.dumps(settings["hooks"]["PostToolUse"])
    assert "ledger-record.sh" in post_commands
    assert "PostToolUseFailure" in settings["hooks"]


def test_managed_assets_include_recorder_files() -> None:
    assets = _aegis_installer._managed_assets(REPO_ROOT, "claude", ("claude",))
    paths = {asset.path for asset in assets}
    assert ".claude/scripts/ledger_lib.py" in paths
    assert ".claude/scripts/ledger-record.sh" in paths
    dispatcher = next(asset for asset in assets if asset.path == ".claude/scripts/ledger-record.sh")
    text = dispatcher.content.decode("utf-8")
    assert "hook record" in text
    assert dispatcher.executable is True


def test_hook_dispatcher_accepts_new_phases() -> None:
    parser = cli.build_arg_parser()
    for phase in ("record", "posttoolusefailure", "sessionstart", "sessionend"):
        args = parser.parse_args(["hook", phase])
        assert args.phase == phase


def test_gitignore_hygiene_report_warns_and_clears(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    reports = repo / ".aegis" / "reports"
    reports.mkdir(parents=True)
    big = reports / "observation-report.json"
    big.write_bytes(b"x" * (_aegis_installer.AEGIS_HYGIENE_SIZE_THRESHOLD_BYTES + 1))
    report = _aegis_installer.gitignore_hygiene_report(repo)
    assert report["gitignore_covers_aegis_output"] is False
    assert report["uncovered_prefixes"]
    assert any("observation-report.json" in warning for warning in report["warnings"])
    (repo / ".gitignore").write_text(".aegis/\n", encoding="utf-8")
    cleared = _aegis_installer.gitignore_hygiene_report(repo)
    assert cleared["gitignore_covers_aegis_output"] is True
    assert cleared["oversized_unignored"] == []
    assert cleared["warnings"] == []


def test_fixture_corpus_covers_documented_fields() -> None:
    posttool = load_fixture_lines("PostToolUse")
    assert any("duration_ms" in fixture for fixture in posttool)
    assert any(fixture.get("agent_id") for fixture in posttool)
    assert all("session_id" in fixture and "transcript_path" in fixture and "cwd" in fixture for fixture in posttool)
    failure = load_fixture_lines("PostToolUseFailure")[0]
    assert "error" in failure and "is_interrupt" in failure
    assert load_fixture_lines("SubagentStop")[0]["agent_type"] == "Explore"
    assert load_fixture_lines("SessionStart")[0]["source"] == "startup"
    assert load_fixture_lines("SessionEnd")[0]["reason"]


def test_assets_and_live_recorder_copies_identical() -> None:
    for rel in (".claude/scripts/gate_lib.py", ".claude/scripts/ledger_lib.py", ".claude/scripts/ledger-record.sh"):
        live = (REPO_ROOT / rel).read_bytes()
        asset = (REPO_ROOT / "aegis_foundation" / "assets" / rel).read_bytes()
        assert live == asset, f"assets/live copies diverge for {rel}"
