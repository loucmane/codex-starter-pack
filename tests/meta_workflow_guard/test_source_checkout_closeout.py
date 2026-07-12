"""Source-checkout completed-work derivation and readiness integration tests."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts._source_workflow_state import (
    SourceWorkflowStateError,
    derive_completed_source_work,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
READINESS_SOURCE = REPO_ROOT / ".claude" / "scripts" / "readiness.sh"
HELPER_SOURCE = REPO_ROOT / "scripts" / "_source_workflow_state.py"
POLICY_EVALUATOR_SOURCE = REPO_ROOT / "scripts" / "aegis-delivery-policy"


def _write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _task_payload(*tasks: tuple[int, str]) -> str:
    return json.dumps(
        {
            "master": {
                "tasks": [
                    {"id": task_id, "title": f"Task {task_id} fixture", "status": status}
                    for task_id, status in tasks
                ]
            }
        }
    )


def _plan_text(task_id: int, status: str = "completed") -> str:
    return f"""---
task_ids: [{task_id}]
---

# Plan - Task {task_id}

| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Scope | evidence | {status} |
| plan-step-implement | Implement | evidence | {status} |
| plan-step-verify | Verify | evidence | {status} |
"""


def _tracker_text(task_id: int, *, status: str = "COMPLETED", checked: bool = True) -> str:
    mark = "x" if checked else " "
    return f"""# Task {task_id} Fixture Tracker

**Status**: {status}

## Plan Compliance Checklist
- [{mark}] plan-step-scope - Scope
- [{mark}] plan-step-implement - Implement
- [{mark}] plan-step-verify - Verify
"""


def _write_source_markers(root: Path) -> None:
    _write(root / "pyproject.toml", '[project]\nname = "aegis-foundation"\n')
    _write(root / "schemas" / "aegis" / "foundation-manifest.schema.json", "{}\n")
    _write(root / "scripts" / "_aegis_installer.py", "# source marker\n")
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(HELPER_SOURCE, root / "scripts" / "_source_workflow_state.py")
    shutil.copy2(POLICY_EVALUATOR_SOURCE, root / "scripts" / "aegis-delivery-policy")
    (root / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(READINESS_SOURCE, root / ".claude" / "scripts" / "readiness.sh")
    packaged_readiness = (
        root / "aegis_foundation" / "assets" / ".claude" / "scripts" / "readiness.sh"
    )
    packaged_readiness.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(READINESS_SOURCE, packaged_readiness)
    _write(root / "aegis_foundation" / "assets" / "scripts" / "codex-guard", "# source marker\n")


def _write_completed_state(root: Path, task_id: int = 99) -> Path:
    _write(root / ".taskmaster" / "tasks" / "tasks.json", _task_payload((task_id, "done")))
    active_root = root / "docs" / "ai" / "work-tracking" / "active"
    active_root.mkdir(parents=True, exist_ok=True)
    archive = (
        root
        / "docs"
        / "ai"
        / "work-tracking"
        / "archive"
        / f"20300101-task{task_id}-source-closeout-COMPLETED"
    )
    tracker = _write(archive / "TRACKER.md", _tracker_text(task_id))

    session = _write(
        root / "sessions" / "2030" / "01" / f"2030-01-01-001-task{task_id}-source-closeout.md",
        f"# Session for Task {task_id}\n",
    )
    session_link = root / "sessions" / "current"
    session_link.symlink_to(session.relative_to(session_link.parent))
    _write(
        root / "sessions" / "state.json",
        json.dumps({"current": session.name, "paused": [], "updated_at": "2030-01-01T00:00:00Z"})
        + "\n",
    )

    plan = _write(
        root / "plans" / f"2030-01-01-task{task_id}-source-closeout.md", _plan_text(task_id)
    )
    plan_link = root / "plans" / "current"
    plan_link.symlink_to(plan.name)
    return tracker


def _write_delivery_policy(root: Path, *, default_branch: str = "main") -> None:
    policy = json.loads((REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8"))
    policy["policy_id"] = "fixture-evidence-gated-v1"
    policy["repository"] = {
        "full_name": "example/aegis",
        "default_branch": default_branch,
        "task_branch_pattern": r"^feat/task-[0-9]+-[a-z0-9-]+$",
    }
    policy["authority"]["issued_by"] = "fixture-owner"
    policy["authority"]["source"] = "source-checkout fixture"
    _write(
        root / "aegis.delivery-policy.json",
        json.dumps(policy, indent=2) + "\n",
    )


def _init_source_repo(tmp_path: Path, task_id: int = 99) -> tuple[Path, Path]:
    root = tmp_path / "source"
    root.mkdir()
    _write_source_markers(root)
    tracker = _write_completed_state(root, task_id)
    subprocess.run(
        ["git", "init", "-b", f"feat/task-{task_id}-source-closeout"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return root, tracker


def _commit_fixture(root: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_readiness(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(root / ".claude" / "scripts" / "readiness.sh"),
            "--root",
            str(root),
            "--all",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _load_guard_module():
    name = "codex_guard_source_closeout_test_module"
    sys.modules.pop(name, None)
    path = REPO_ROOT / "scripts" / "codex-guard"
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def test_completed_source_work_requires_all_authorities(tmp_path: Path) -> None:
    root, tracker = _init_source_repo(tmp_path)

    state = derive_completed_source_work(root, "feat/task-99-source-closeout")

    assert state is not None
    assert state.task_id == "99"
    assert state.tracker_path == tracker.resolve()


def test_completed_source_work_derives_taskless_default_branch_from_current_pointers(
    tmp_path: Path,
) -> None:
    root, tracker = _init_source_repo(tmp_path)
    _write_delivery_policy(root)

    state = derive_completed_source_work(root, "main")

    assert state is not None
    assert state.task_id == "99"
    assert state.branch == "main"
    assert state.tracker_path == tracker.resolve()


def test_taskless_default_branch_derivation_requires_policy_opt_in(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)

    assert derive_completed_source_work(root, "main") is None


def test_taskless_default_branch_derivation_rejects_invalid_or_inactive_policy(
    tmp_path: Path,
) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write(root / "aegis.delivery-policy.json", "not-json\n")
    with pytest.raises(SourceWorkflowStateError, match="invalid JSON"):
        derive_completed_source_work(root, "main")

    _write_delivery_policy(root)
    policy_path = root / "aegis.delivery-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["authority"]["status"] = "revoked"
    policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")
    with pytest.raises(SourceWorkflowStateError, match="authority is not active"):
        derive_completed_source_work(root, "main")


def test_taskless_default_branch_derivation_rejects_schema_invalid_policy(
    tmp_path: Path,
) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write_delivery_policy(root)
    policy_path = root / "aegis.delivery-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["unexpected_authority"] = True
    policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")

    with pytest.raises(SourceWorkflowStateError, match="unknown fields"):
        derive_completed_source_work(root, "main")


def test_taskless_default_branch_derivation_rejects_stale_session_identity(
    tmp_path: Path,
) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write_delivery_policy(root)
    session_link = root / "sessions" / "current"
    session_link.unlink()
    stale_session = _write(
        root / "sessions" / "2030" / "01" / "2030-01-01-002-task98-stale.md",
        "# Session for Task 98\n",
    )
    session_link.symlink_to(stale_session.relative_to(session_link.parent))

    with pytest.raises(SourceWorkflowStateError, match="does not reference Task 99"):
        derive_completed_source_work(root, "main")


def test_taskless_default_branch_derivation_rejects_pointer_escape(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write_delivery_policy(root)
    outside = _write(tmp_path / "outside-plan.md", _plan_text(99))
    plan_link = root / "plans" / "current"
    plan_link.unlink()
    plan_link.symlink_to(outside)

    with pytest.raises(SourceWorkflowStateError, match="resolves outside plans"):
        derive_completed_source_work(root, "main")


def test_completed_source_work_rejects_non_done_task(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write(root / ".taskmaster" / "tasks" / "tasks.json", _task_payload((99, "in-progress")))

    with pytest.raises(SourceWorkflowStateError, match="expected 'done'"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")


def test_completed_source_work_rejects_ambiguous_archives(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    second = root / "docs" / "ai" / "work-tracking" / "archive" / "20300102-task99-second-COMPLETED"
    _write(second / "TRACKER.md", _tracker_text(99))

    with pytest.raises(SourceWorkflowStateError, match="exactly one completed archive"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")


def test_completed_source_work_rejects_missing_archive_and_tracker(tmp_path: Path) -> None:
    root, tracker = _init_source_repo(tmp_path)
    shutil.rmtree(tracker.parent)
    with pytest.raises(SourceWorkflowStateError, match="found 0"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")

    tracker.parent.mkdir(parents=True)
    with pytest.raises(SourceWorkflowStateError, match="tracker is missing"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")


def test_completed_source_work_defers_to_active_envelope(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    active = root / "docs" / "ai" / "work-tracking" / "active" / "20300102-task99-active-ACTIVE"
    _write(active / "TRACKER.md", _tracker_text(99, status="ACTIVE", checked=False))

    assert derive_completed_source_work(root, "feat/task-99-source-closeout") is None


def test_completed_source_work_rejects_tracker_identity_and_status(tmp_path: Path) -> None:
    root, tracker = _init_source_repo(tmp_path)
    tracker.write_text(_tracker_text(98), encoding="utf-8")
    with pytest.raises(SourceWorkflowStateError, match="does not reference Task 99"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")

    tracker.write_text(_tracker_text(99, status="ACTIVE"), encoding="utf-8")
    with pytest.raises(SourceWorkflowStateError, match="status is not COMPLETED"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")


def test_completed_source_work_rejects_archive_symlink(tmp_path: Path) -> None:
    root, tracker = _init_source_repo(tmp_path)
    shutil.rmtree(tracker.parent)
    outside = tmp_path / "outside" / "20300101-task99-source-closeout-COMPLETED"
    _write(outside / "TRACKER.md", _tracker_text(99))
    tracker.parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(SourceWorkflowStateError, match="must not be a symlink"):
        derive_completed_source_work(root, "feat/task-99-source-closeout")


def test_completed_source_work_never_overrides_installed_state(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write(root / ".aegis" / "foundation-manifest.json", "{}\n")
    assert derive_completed_source_work(root, "feat/task-99-source-closeout") is None

    (root / ".aegis" / "foundation-manifest.json").unlink()
    _write(root / ".aegis" / "state" / "current-work.json", "{}\n")
    assert derive_completed_source_work(root, "feat/task-99-source-closeout") is None


def test_clean_source_checkout_readiness_accepts_completed_archive(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _commit_fixture(root)

    result = _run_readiness(root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert "completed source tracker derived" in result.stdout
    assert "completed plan and tracker steps align" in result.stdout
    assert not (root / ".aegis" / "state" / "current-work.json").exists()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout == ""


def test_clean_source_checkout_readiness_accepts_completed_archive_on_default_branch(
    tmp_path: Path,
) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write_delivery_policy(root)
    subprocess.run(
        ["git", "branch", "-m", "main"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    _commit_fixture(root)

    result = _run_readiness(root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert "completed source tracker derived" in result.stdout


def test_installed_target_readiness_does_not_use_source_archive(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    _write(root / ".aegis" / "foundation-manifest.json", "{}\n")

    result = _run_readiness(root)

    assert result.returncode == 2
    assert "Taskmaster Task 99 status is 'done', expected 'in-progress'" in result.stdout
    assert "completed source tracker derived" not in result.stdout


def test_completed_source_readiness_rejects_incomplete_plan(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    plan_link = root / "plans" / "current"
    plan_link.resolve().write_text(_plan_text(99, "pending"), encoding="utf-8")

    result = _run_readiness(root)

    assert result.returncode == 2
    assert "completed source plan has plan-step-scope='pending'" in result.stdout


def test_guard_uses_same_completed_source_tracker(monkeypatch, tmp_path: Path) -> None:
    root, tracker = _init_source_repo(tmp_path)
    module = _load_guard_module()
    active_root = root / "docs" / "ai" / "work-tracking" / "active"
    archive_root = root / "docs" / "ai" / "work-tracking" / "archive"
    monkeypatch.setattr(module, "REPO_ROOT", root)
    monkeypatch.setattr(module, "WORK_TRACKING_PREFIX", active_root)
    monkeypatch.setattr(module, "WORK_TRACKING_ARCHIVE_BASE", archive_root)
    monkeypatch.setattr(module, "CURRENT_WORK_STATE_PATH", root / ".aegis/state/current-work.json")
    monkeypatch.setattr(module, "get_current_branch", lambda: "feat/task-99-source-closeout")

    assert module.get_active_tracker_path() == tracker.resolve()


def test_completed_archive_can_hand_off_to_next_active_task(tmp_path: Path) -> None:
    root, _tracker = _init_source_repo(tmp_path)
    subprocess.run(
        ["git", "switch", "-c", "feat/task-100-next-work"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    _write(
        root / ".taskmaster" / "tasks" / "tasks.json",
        _task_payload((99, "done"), (100, "in-progress")),
    )
    active = root / "docs" / "ai" / "work-tracking" / "active" / "20300102-task100-next-ACTIVE"
    _write(active / "TRACKER.md", _tracker_text(100, status="ACTIVE", checked=False))

    session_link = root / "sessions" / "current"
    session_link.unlink()
    session = _write(
        root / "sessions" / "2030" / "01" / "2030-01-02-001-task100-next.md",
        "# Session for Task 100\n",
    )
    session_link.symlink_to(session.relative_to(session_link.parent))
    _write(
        root / "sessions" / "state.json",
        json.dumps({"current": session.name, "paused": [], "updated_at": "2030-01-02T00:00:00Z"})
        + "\n",
    )
    plan_link = root / "plans" / "current"
    plan_link.unlink()
    plan = _write(root / "plans" / "2030-01-02-task100-next.md", _plan_text(100, "pending"))
    plan_link.symlink_to(plan.name)

    result = _run_readiness(root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert "Required Taskmaster Task 100 is in-progress" in result.stdout
    assert "ACTIVE folder '20300102-task100-next-ACTIVE' matches Task 100" in result.stdout
