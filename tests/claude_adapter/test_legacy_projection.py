"""TM-233 legacy S:W:H:E projection tests.

Old workflow files remain useful, but the passive ledger is the source of truth.
These tests guard the generated-block contract so projection can coexist with
human-authored tracker/session/plan content.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from aegis_foundation import legacy_projection


REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_LIB = REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"


def load_ledger_lib():
    spec = importlib.util.spec_from_file_location("ledger_lib_for_legacy_projection", LEDGER_LIB)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ledger_lib_for_legacy_projection"] = module
    spec.loader.exec_module(module)
    return module


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, check=False)


def make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    result = run(["git", "init", "-q"], path)
    assert result.returncode == 0, result.stderr
    return path


def event(event_id: str, event_type: str, **updates: object) -> dict[str, object]:
    base: dict[str, object] = {
        "event_id": event_id,
        "event_type": event_type,
        "session_id": "sess-233",
        "branch": "feat/task-233-legacy-shadow-projection",
        "extra": {},
    }
    base.update(updates)
    return base


def test_projection_preserves_human_content_and_is_idempotent(tmp_path: Path) -> None:
    output = tmp_path / "TRACKER.md"
    output.write_text("# Tracker\n\nHuman note stays.\n", encoding="utf-8")
    events = [
        event("evt-1", "scope", extra={"task_id": "233", "path_globs": ["docs/aegis/**"]}),
        event("evt-2", "verification", extra={"package": "aegis", "gate": "pytest", "commit": "abc123"}, exit_class="pass"),
    ]

    first = legacy_projection.project_to_file(events, output)
    first_text = output.read_text(encoding="utf-8")
    second = legacy_projection.project_to_file(events, output)
    second_text = output.read_text(encoding="utf-8")

    assert first.changed is True
    assert second.changed is False
    assert first_text == second_text
    assert "# Tracker" in second_text
    assert "Human note stays." in second_text
    assert second_text.count(legacy_projection.BEGIN_MARKER) == 1
    assert second_text.count(legacy_projection.END_MARKER) == 1
    assert "[S:sess-233 W:task-233 H:scope E:ledger:evt-1]" in second_text
    assert "[S:sess-233 W:feat/task-233-legacy-shadow-projection H:verify E:ledger:evt-2]" in second_text


def test_projection_replaces_only_existing_generated_block() -> None:
    old_section = legacy_projection.render_section([event("old", "task_truth", extra={"task_id": "1", "status": "done"})])
    original = f"before\n\n{old_section}\nafter\n"
    new_section = legacy_projection.render_section(
        [event("new", "delivery", extra={"action": "opened PR"})]
    )

    updated, changed = legacy_projection.apply_generated_section(original, new_section)

    assert changed is True
    assert "before" in updated
    assert "after" in updated
    assert "ledger:old" not in updated
    assert "ledger:new" in updated
    assert updated.count(legacy_projection.BEGIN_MARKER) == 1


def test_projection_filters_low_level_events_by_default() -> None:
    events = [
        event("m1", "mutation", tool_name="Bash", paths=["app.py"]),
        event("g1", "gate_decision", extra={"verdict": "would_block"}),
        event("v1", "verification", extra={"package": "app", "gate": "test"}),
        event("t1", "task_truth", extra={"task_id": "233", "status": "done"}),
    ]

    default = legacy_projection.projectable_events(events)
    all_events = legacy_projection.projectable_events(
        events,
        include_mutations=True,
        include_gate_decisions=True,
    )

    assert [item["event_id"] for item in default] == ["v1", "t1"]
    assert [item["event_id"] for item in all_events] == ["m1", "g1", "v1", "t1"]


def test_cli_project_sweh_reads_ledger_and_updates_output(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    state_home = tmp_path / "state"
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state_home.as_posix()
    ledger_lib = load_ledger_lib()
    ledger = ledger_lib.open_ledger(cwd=repo, env=env)
    try:
        ledger.append(
            {
                "event_type": "mutation",
                "session_id": "sess-cli",
                "branch": "feat/task-233-legacy-shadow-projection",
                "tool_name": "Bash",
                "extra": {"command": "echo should-not-be-projected"},
            }
        )
        ledger.append(
            {
                "event_type": "verification",
                "session_id": "sess-cli",
                "branch": "feat/task-233-legacy-shadow-projection",
                "extra": {"package": "aegis", "gate": "pytest", "commit": "abc1234"},
                "exit_class": "pass",
            }
        )
        ledger.append(
            {
                "event_type": "task_truth",
                "session_id": "sess-cli",
                "branch": "feat/task-233-legacy-shadow-projection",
                "extra": {"task_id": "233", "status": "in-progress"},
            }
        )
    finally:
        ledger.close()

    output = "docs/ai/work-tracking/active/task-233/TRACKER.md"
    result = run(
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            REPO_ROOT.as_posix(),
            "ledger",
            "project-sweh",
            "--target-dir",
            repo.as_posix(),
            "--output",
            output,
            "--json",
        ],
        REPO_ROOT,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "applied"
    assert payload["event_count"] == 2
    assert payload["changed"] is True
    rendered = (repo / output).read_text(encoding="utf-8")
    assert legacy_projection.BEGIN_MARKER in rendered
    assert "[S:sess-cli W:feat/task-233-legacy-shadow-projection H:verify" in rendered
    assert "[S:sess-cli W:task-233 H:task-truth" in rendered
    assert "should-not-be-projected" not in rendered


def test_cli_project_sweh_active_updates_existing_legacy_surfaces(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    state_home = tmp_path / "state"
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state_home.as_posix()
    session = repo / "sessions" / "2026" / "07" / "task-233.md"
    plan = repo / "plans" / "2026-07-task-233.md"
    work = repo / "docs" / "ai" / "work-tracking" / "active" / "20260709-task233-ACTIVE"
    for path in (session, plan, work / "TRACKER.md", work / "HANDOFF.md"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.name}\n\nHuman content.\n", encoding="utf-8")
    (repo / ".aegis" / "state").mkdir(parents=True, exist_ok=True)
    (repo / ".aegis" / "state" / "current-work.json").write_text(
        json.dumps(
            {
                "mode": "task",
                "task": {
                    "id": "233",
                    "slug": "legacy-shadow-projection",
                    "status": "in-progress",
                },
                "paths": {
                    "session": "sessions/2026/07/task-233.md",
                    "plan": "plans/2026-07-task-233.md",
                    "work_tracking": "docs/ai/work-tracking/active/20260709-task233-ACTIVE",
                }
            }
        ),
        encoding="utf-8",
    )
    ledger_lib = load_ledger_lib()
    ledger = ledger_lib.open_ledger(cwd=repo, env=env)
    try:
        ledger.append(
            {
                "event_type": "scope",
                "event_id": "scope-233",
                "session_id": "sess-active",
                "branch": "feat/task-233-legacy-shadow-projection",
                "extra": {"task_id": "233", "path_globs": ["aegis_foundation/**"]},
            }
        )
        ledger.append(
            {
                "event_type": "verification",
                "event_id": "verify-233",
                "session_id": "sess-active",
                "branch": "feat/task-233-legacy-shadow-projection",
                "extra": {"package": "aegis", "gate": "pytest", "commit": "def5678"},
                "exit_class": "pass",
            }
        )
    finally:
        ledger.close()

    result = run(
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            REPO_ROOT.as_posix(),
            "ledger",
            "project-sweh",
            "--target-dir",
            repo.as_posix(),
            "--active",
            "--json",
        ],
        REPO_ROOT,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["event_count"] == 2
    assert payload["output_path"] is None
    assert sorted(Path(path).name for path in payload["output_paths"]) == [
        "2026-07-task-233.md",
        "HANDOFF.md",
        "TRACKER.md",
        "task-233.md",
    ]
    for path in (session, plan, work / "TRACKER.md", work / "HANDOFF.md"):
        rendered = path.read_text(encoding="utf-8")
        assert "Human content." in rendered
        assert legacy_projection.BEGIN_MARKER in rendered
        assert "ledger:scope-233" in rendered
        assert "ledger:verify-233" in rendered


def test_cli_project_sweh_requires_an_output_or_active_surfaces(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    result = run(
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            REPO_ROOT.as_posix(),
            "ledger",
            "project-sweh",
            "--target-dir",
            repo.as_posix(),
        ],
        REPO_ROOT,
        env=env,
    )

    assert result.returncode == 1
    assert "requires --output or --active" in result.stderr


def test_scope_set_can_project_active_sweh_surfaces(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    branch_result = run(["git", "switch", "-c", "feat/task-233-legacy-shadow-projection"], repo)
    assert branch_result.returncode == 0, branch_result.stderr
    state_home = tmp_path / "state"
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state_home.as_posix()
    session = repo / "sessions" / "2026" / "07" / "task-233.md"
    plan = repo / "plans" / "2026-07-task-233.md"
    work = repo / "docs" / "ai" / "work-tracking" / "active" / "20260709-task233-ACTIVE"
    for path in (session, plan, work / "TRACKER.md"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.name}\n\nHuman content.\n", encoding="utf-8")
    (repo / ".aegis" / "state").mkdir(parents=True, exist_ok=True)
    (repo / ".aegis" / "state" / "current-work.json").write_text(
        json.dumps(
            {
                "mode": "task",
                "task": {
                    "id": "233",
                    "slug": "legacy-shadow-projection",
                    "status": "in-progress",
                },
                "paths": {
                    "session": "sessions/2026/07/task-233.md",
                    "plan": "plans/2026-07-task-233.md",
                    "work_tracking": "docs/ai/work-tracking/active/20260709-task233-ACTIVE",
                }
            }
        ),
        encoding="utf-8",
    )

    result = run(
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            REPO_ROOT.as_posix(),
            "scope",
            "set",
            "233",
            "aegis_foundation/**",
            "--target-dir",
            repo.as_posix(),
            "--project-sweh",
        ],
        REPO_ROOT,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert "Scope recorded for branch feat/task-233-legacy-shadow-projection: task 233" in result.stdout
    assert "Legacy S:W:H:E projection: applied (3 surfaces, changed=True)" in result.stdout
    for path in (session, plan, work / "TRACKER.md"):
        rendered = path.read_text(encoding="utf-8")
        assert "Human content." in rendered
        assert legacy_projection.BEGIN_MARKER in rendered
        assert "Scope recorded for 233. Paths: aegis_foundation/**." in rendered
        assert "[S:task-233 W:task-233-legacy-shadow-projection H:scope" in rendered
