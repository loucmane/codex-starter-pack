from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from aegis_foundation import worktree_capture_audit as audit

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "aegis" / "worktree-capture-audit.json"
LIVE_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "aegis" / "worktree-subagent-live-coverage.json"
)


def run(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, cwd=cwd, capture_output=True, text=True, check=False)


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    assert run(["git", "init", "-q"], repo).returncode == 0
    assert run(["git", "config", "user.name", "Task 239"], repo).returncode == 0
    assert run(["git", "config", "user.email", "task239@example.invalid"], repo).returncode == 0
    assets = {
        ".aegis/bin/aegis": "#!/usr/bin/env bash\nexit 0\n",
        ".claude/scripts/ledger-record.sh": "#!/usr/bin/env bash\nexit 0\n",
        ".claude/scripts/gate_lib.py": "# fixture\n",
        ".claude/scripts/ledger_lib.py": "# fixture\n",
        ".claude/settings.json": json.dumps(
            {
                "hooks": {
                    "SessionStart": [{}],
                    "PostToolUse": [{}],
                    "PostToolUseFailure": [{}],
                    "Stop": [{}],
                }
            }
        ),
        "README.md": "fixture\n",
    }
    for relative, content in assets.items():
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    assert run(["git", "add", "."], repo).returncode == 0
    assert run(["git", "commit", "-qm", "fixture"], repo).returncode == 0
    return repo


def test_replay_fixture_covers_every_cause_and_status() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report = audit.replay_fixture(payload)

    assert report["summary"]["scenario_count"] == 10
    assert report["summary"]["status_counts"] == {
        "supported": 1,
        "unsupported": 2,
        "degraded": 3,
        "failed": 4,
    }
    assert report["summary"]["cause_counts"] == {cause: 1 for cause in audit.CAUSE_CODES}
    assert [scenario["scenario_id"] for scenario in report["scenarios"]] == [
        scenario["scenario_id"] for scenario in payload["scenarios"]
    ]
    audit.assert_secret_free(report)


def test_two_linked_worktrees_share_repository_identity_and_ledger_path(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    worktree = tmp_path / "linked-worktree"
    state_home = tmp_path / "state"
    assert run(
        ["git", "worktree", "add", "-q", "-b", "fixture/worktree-a", worktree.as_posix()],
        repo,
    ).returncode == 0
    try:
        parent = audit.collect_snapshot(
            repo,
            source_root=REPO_ROOT,
            scenario_id="parent",
            client_name="codex",
            client_version="fixture",
            worktree_label="<worktree-parent>",
            state_home=state_home,
        )
        child = audit.collect_snapshot(
            worktree,
            source_root=REPO_ROOT,
            scenario_id="child",
            client_name="claude",
            client_version="fixture",
            worktree_label="<worktree-child>",
            state_home=state_home,
        )
    finally:
        assert run(["git", "worktree", "remove", worktree.as_posix()], repo).returncode == 0

    assert parent["repository"] == child["repository"]
    assert parent["ledger"]["resolved_path"] == child["ledger"]["resolved_path"]
    assert parent["worktree"]["branch"] != child["worktree"]["branch"]
    assert parent["assets"]["checksums"] == child["assets"]["checksums"]
    assert all(value == "supported" for value in child["hooks"].values())
    assert not state_home.exists(), "read-only snapshots must not initialize ledger state"


def test_concurrent_worktree_writers_survive_teardown(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    worktrees = [tmp_path / "worktree-a", tmp_path / "worktree-b"]
    state_home = tmp_path / "state"
    for index, worktree in enumerate(worktrees, start=1):
        assert run(
            [
                "git",
                "worktree",
                "add",
                "-q",
                "-b",
                f"fixture/concurrent-{index}",
                worktree.as_posix(),
            ],
            repo,
        ).returncode == 0

    ledger_lib = audit.load_ledger_module(REPO_ROOT)

    def append_events(worktree: Path, label: str) -> list[str]:
        ledger = ledger_lib.open_ledger(
            cwd=worktree,
            env={"XDG_STATE_HOME": state_home.as_posix()},
        )
        try:
            return [
                ledger.append(
                    {
                        "session_id": f"session-{label}",
                        "branch": f"fixture/{label}",
                        "cwd": worktree.as_posix(),
                        "event_type": "mutation",
                        "tool_name": "Write",
                        "outcome": "pass",
                        "agent_id": f"agent-{label}",
                        "agent_type": "fixture-child",
                        "extra": {},
                    }
                )["event_id"]
                for _ in range(12)
            ]
        finally:
            ledger.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(append_events, worktree, f"child-{index}")
                for index, worktree in enumerate(worktrees, start=1)
            ]
            expected_ids = {event_id for future in futures for event_id in future.result()}

        snapshots = [
            audit.collect_snapshot(
                worktree,
                source_root=REPO_ROOT,
                scenario_id=f"concurrent-{index}",
                client_name="fixture",
                client_version="1",
                worktree_label=f"<worktree-{index}>",
                state_home=state_home,
            )
            for index, worktree in enumerate(worktrees, start=1)
        ]
    finally:
        for worktree in worktrees:
            assert run(["git", "worktree", "remove", worktree.as_posix()], repo).returncode == 0

    after_teardown = audit.collect_snapshot(
        repo,
        source_root=REPO_ROOT,
        scenario_id="after-teardown",
        client_name="fixture",
        client_version="1",
        worktree_label="<worktree-primary>",
        state_home=state_home,
    )
    assert len(expected_ids) == 24
    assert all(snapshot["repository"] == snapshots[0]["repository"] for snapshot in snapshots)
    assert all(
        snapshot["ledger"]["resolved_path"] == snapshots[0]["ledger"]["resolved_path"]
        for snapshot in snapshots
    )
    assert expected_ids == set(after_teardown["event_window"]["event_ids"])


def test_live_coverage_fixture_is_secret_free_and_preserves_observed_outcomes() -> None:
    payload = json.loads(LIVE_FIXTURE.read_text(encoding="utf-8"))

    audit.assert_secret_free(payload)
    assert payload["schema_version"] == audit.SCHEMA_VERSION
    assert [scenario["scenario_id"] for scenario in payload["scenarios"]] == [
        "shared-store-lifecycle",
        "claude-default-state",
        "claude-writable-state",
        "codex-linked-worktree",
    ]
    assert [scenario["result"]["status"] for scenario in payload["scenarios"]] == [
        "supported",
        "failed",
        "degraded",
        "unsupported",
    ]
    assert payload["scenarios"][0]["teardown"]["missing_event_count"] == 0
    assert payload["scenarios"][2]["capture"]["child_mutations"] == 2
    assert payload["scenarios"][2]["attribution"]["parent_agent_id"] == "missing"
    assert payload["scenarios"][3]["capture"]["nested_session_events"] == 0


def test_snapshot_reads_existing_ledger_without_leaking_live_identifiers(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state_home = tmp_path / "state"
    ledger_lib = audit.load_ledger_module(REPO_ROOT)
    ledger = ledger_lib.open_ledger(cwd=repo, env={"XDG_STATE_HOME": state_home.as_posix()})
    try:
        recorded = ledger.append(
            {
                "session_id": "live-session-id",
                "branch": "fixture/branch",
                "cwd": repo.as_posix(),
                "event_type": "mutation",
                "tool_name": "Write",
                "outcome": "pass",
                "agent_id": "live-child-id",
                "agent_type": "Explore",
                "extra": {
                    "repository_identity": "sha256:fixture",
                    "worktree_root": repo.as_posix(),
                    "head": "a" * 40,
                    "parent_agent_id": "live-parent-id",
                },
            }
        )
    finally:
        ledger.close()

    before_mtime = next((state_home / "aegis").glob("*/ledger.db")).stat().st_mtime_ns
    snapshot = audit.collect_snapshot(
        repo,
        source_root=REPO_ROOT,
        scenario_id="ledger-read",
        client_name="claude",
        client_version="fixture",
        worktree_label="<worktree-child>",
        state_home=state_home,
        child_session_id="live-session-id",
        child_agent_id="live-child-id",
        parent_agent_link="live-parent-id",
    )
    after_mtime = next((state_home / "aegis").glob("*/ledger.db")).stat().st_mtime_ns

    assert snapshot["event_window"]["event_ids"] == [recorded["event_id"]]
    assert snapshot["events"][0]["cwd"] == "<event-cwd>"
    assert snapshot["events"][0]["worktree_root"] == "<event-worktree>"
    rendered = json.dumps(snapshot, sort_keys=True)
    assert "live-session-id" not in rendered
    assert "live-child-id" not in rendered
    assert "live-parent-id" not in rendered
    assert repo.as_posix() not in rendered
    assert before_mtime == after_mtime
    audit.assert_secret_free(snapshot)


@pytest.mark.parametrize(
    "payload,match",
    [
        ({"prompt": "raw"}, "prompt/transcript"),
        ({"value": "/home/person/private/file"}, "absolute home"),
        ({"value": "Authorization: secret"}, "secret-shaped"),
    ],
)
def test_secret_free_validator_rejects_unsafe_checked_in_evidence(
    payload: dict[str, str], match: str
) -> None:
    with pytest.raises(audit.AuditError, match=match):
        audit.assert_secret_free(payload)


def test_replay_cli_writes_only_the_requested_output(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    assert audit.main(["replay", "--fixture", FIXTURE.as_posix(), "--output", output.as_posix()]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["scenario_count"] == 10
    assert sorted(path.name for path in tmp_path.iterdir()) == ["report.json"]
