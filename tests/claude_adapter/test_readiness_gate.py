from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from aegis_foundation import task_authority


REPO_ROOT = Path(__file__).resolve().parents[2]
READINESS = REPO_ROOT / ".claude" / "scripts" / "readiness.sh"


def run(
    cmd: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(tmp_path: Path, *, task_id: int = 103, branch: str | None = None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert run(["git", "init", "-q"], repo).returncode == 0
    branch = branch or f"feat/task-{task_id}-claude-runtime-adapter"
    assert run(["git", "checkout", "-q", "-b", branch], repo).returncode == 0

    write(
        repo / ".taskmaster" / "tasks" / "tasks.json",
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": task_id,
                            "title": "Claude Runtime Adapter",
                            "status": "in-progress",
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
    )
    write(repo / ".taskmaster" / "state.json", json.dumps({"currentTag": "master"}))

    session_rel = Path("2026/05/2026-05-06-002-task103-claude-runtime-adapter.md")
    write(
        repo / "sessions" / session_rel,
        f"---\nsession_id: 2026-05-06-002\n---\n\n# Task {task_id} Session\n",
    )
    (repo / "sessions" / "current").symlink_to(session_rel)
    write(
        repo / "sessions" / "state.json",
        json.dumps({"current": session_rel.name, "paused": [], "updated_at": "2026-05-06T17:10:09+02:00"}),
    )

    plan_rel = Path(f"2026-05-06-task{task_id}-claude-runtime-adapter.md")
    write(
        repo / "plans" / plan_rel,
        f"""---
task_ids: [{task_id}]
---

# Plan - Task {task_id}

| Step ID | Description | Evidence | Status |
| --- | --- | --- | --- |
| plan-step-scope | Scope | evidence | completed |
| plan-step-implement | Implement | evidence | pending |
| plan-step-verify | Verify | evidence | pending |
| plan-step-emergency | Emergency | evidence | n/a |
""",
    )
    (repo / "plans" / "current").symlink_to(plan_rel)

    active = repo / "docs" / "ai" / "work-tracking" / "active" / f"20260506-task{task_id}-claude-runtime-adapter-ACTIVE"
    write(
        active / "TRACKER.md",
        f"""# Task {task_id} Claude Runtime Adapter Tracker

## Plan Compliance Checklist
- [x] plan-step-scope - Scope
- [ ] plan-step-implement - Implement
- [ ] plan-step-verify - Verify
- [ ] plan-step-emergency (if applicable)
""",
    )
    return repo


def readiness(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["bash", str(READINESS), "--root", str(repo), *args], repo)


def write_aegis_current_work(repo: Path, *, task_id: int = 103, taskmaster_required: bool = False) -> None:
    write(
        repo / ".aegis" / "state" / "current-work.json",
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "in-progress",
                "task": {
                    "id": str(task_id),
                    "slug": "claude-runtime-adapter",
                    "title": "Claude Runtime Adapter",
                    "status": "in-progress",
                },
                "integrations": {
                    "taskmaster": {
                        "required": taskmaster_required,
                        "detected": True,
                    },
                    "serena": {
                        "required": False,
                        "detected": False,
                    },
                },
            }
        ),
    )


def make_beads_repo(
    tmp_path: Path,
    *,
    branch: str = "polecat/ags-0103",
    bead_status: str = "in_progress",
) -> tuple[Path, dict[str, str]]:
    repo = make_repo(tmp_path)
    assert run(["git", "branch", "-m", branch], repo).returncode == 0
    bead_id = "ags-0103"

    session_path = (repo / "sessions" / "current").resolve()
    session_path.write_text(f"# Bead {bead_id} Session\n", encoding="utf-8")
    plan_path = (repo / "plans" / "current").resolve()
    plan_path.write_text(
        f"""---
task_ids: [{bead_id}]
---

# Plan - Bead {bead_id}

| Step ID | Description | Evidence | Status |
| --- | --- | --- | --- |
| plan-step-scope | Scope | evidence | completed |
| plan-step-implement | Implement | evidence | pending |
| plan-step-verify | Verify | evidence | pending |
| plan-step-emergency | Emergency | evidence | n/a |
""",
        encoding="utf-8",
    )
    active_root = repo / "docs" / "ai" / "work-tracking" / "active"
    old_active = next(path for path in active_root.iterdir() if path.is_dir())
    active = active_root / "20260506-ags-0103-claude-runtime-adapter-ACTIVE"
    old_active.rename(active)
    (active / "TRACKER.md").write_text(
        f"""# Bead {bead_id} Claude Runtime Adapter Tracker

## Plan Compliance Checklist
- [x] plan-step-scope - Scope
- [ ] plan-step-implement - Implement
- [ ] plan-step-verify - Verify
- [ ] plan-step-emergency (if applicable)
""",
        encoding="utf-8",
    )

    evidence = task_authority.TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=hashlib.sha256(b"snapshot").hexdigest(),
        migration_report_sha256=hashlib.sha256(b"migration").hexdigest(),
        backup_restore_report_sha256=hashlib.sha256(b"restore").hexdigest(),
    )
    receipt_path = tmp_path / "authority" / "aegis.json"
    initial = task_authority.initialize_taskmaster_authority(
        receipt_path,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        evidence=evidence,
        activated_at="2026-07-15T18:00:00Z",
    )
    receipt = task_authority.transition_authority(
        receipt_path,
        target_mode=task_authority.TaskAuthorityMode.BEADS,
        expected_generation=initial.generation,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
        expected_evidence=evidence,
        activated_at="2026-07-15T18:01:00Z",
    )
    write(
        repo / ".aegis" / "state" / "current-work.json",
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "in-progress",
                "task": {
                    "id": bead_id,
                    "slug": "claude-runtime-adapter",
                    "title": "Claude Runtime Adapter",
                    "status": "in-progress",
                    "source": "beads",
                },
                "authority": {
                    "mode": "beads",
                    "rig": "aegis",
                    "beads_prefix": "ags",
                    "database": "aegis_beads",
                    "receipt_generation": receipt.generation,
                    "receipt_sha256": task_authority.receipt_sha256(receipt),
                },
                "integrations": {
                    "taskmaster": {"required": False, "detected": True},
                    "serena": {"required": False, "detected": False},
                },
            }
        ),
    )

    fake_bd = tmp_path / "bin" / "bd"
    write(
        fake_bd,
        """#!/usr/bin/env python3
import json
import os
import sys

if sys.argv[1:] == ["--version"]:
    print("bd version 1.1.0 (fixture)")
    raise SystemExit(0)
if "--readonly" not in sys.argv or "--json" not in sys.argv:
    print("readonly flags missing", file=sys.stderr)
    raise SystemExit(9)
issue_id = sys.argv[sys.argv.index("--id") + 1]
print(json.dumps([{"id": issue_id, "status": os.environ["FAKE_BD_STATUS"]}]))
""",
    )
    fake_bd.chmod(0o755)
    bd_digest = hashlib.sha256(fake_bd.read_bytes()).hexdigest()
    authority_runtime = tmp_path / "trusted-runtime" / "task_authority.py"
    write(
        authority_runtime,
        Path(task_authority.__file__).read_text(encoding="utf-8"),
    )
    authority_runtime.chmod(0o444)
    authority_runtime_digest = hashlib.sha256(authority_runtime.read_bytes()).hexdigest()
    env = {
        **os.environ,
        "AEGIS_TASK_AUTHORITY_FILE": str(receipt_path),
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE": str(authority_runtime),
        "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256": authority_runtime_digest,
        "GC_RIG": "aegis",
        "GC_BEADS_PREFIX": "ags",
        "BEADS_DOLT_SERVER_DATABASE": "aegis_beads",
        "AEGIS_BD_EXECUTABLE": str(fake_bd),
        "AEGIS_BD_SHA256": bd_digest,
        "FAKE_BD_STATUS": bead_status,
    }
    return repo, env


def beads_readiness(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return run(
        ["bash", str(READINESS), "--root", str(repo), "--all"],
        repo,
        env=env,
    )


def test_ready_when_task_session_plan_and_tracker_align(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    result = readiness(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert "Taskmaster Task 103 is in-progress" in result.stdout
    assert "plan-step statuses align" in result.stdout


def test_beads_readiness_accepts_polecat_branch_and_ignores_taskmaster_rollback_copy(
    tmp_path: Path,
) -> None:
    repo, env = make_beads_repo(tmp_path)
    tasks_path = repo / ".taskmaster" / "tasks" / "tasks.json"
    tasks_path.write_text("not authoritative\n", encoding="utf-8")

    result = beads_readiness(repo, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert "branch 'polecat/ags-0103' maps to Bead ags-0103" in result.stdout
    assert "authoritative Bead ags-0103 is in_progress via pinned read-only bd" in result.stdout
    assert "receipt generation 2" in result.stdout


def test_beads_readiness_accepts_persistent_gas_city_branch(tmp_path: Path) -> None:
    repo, env = make_beads_repo(tmp_path, branch="gc-polecat-012345abcdef")

    result = beads_readiness(repo, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "persistent Gas City branch 'gc-polecat-012345abcdef' uses current-work Bead ags-0103" in result.stdout


def test_beads_readiness_rejects_non_in_progress_authoritative_bead(tmp_path: Path) -> None:
    repo, env = make_beads_repo(tmp_path, bead_status="closed")

    result = beads_readiness(repo, env)

    assert result.returncode == 2
    assert "authoritative Bead ags-0103 status is 'closed', expected 'in_progress'" in result.stdout


def test_beads_readiness_rejects_branch_and_receipt_binding_drift(tmp_path: Path) -> None:
    repo, env = make_beads_repo(tmp_path, branch="polecat/ags-9999")
    current_work_path = repo / ".aegis" / "state" / "current-work.json"
    current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
    current_work["authority"]["receipt_generation"] = 99
    current_work_path.write_text(json.dumps(current_work), encoding="utf-8")

    result = beads_readiness(repo, env)

    assert result.returncode == 2
    assert "authority record does not exactly match" in result.stdout
    assert "polecat branch names Bead 'ags-9999', but current work names 'ags-0103'" in result.stdout


def test_beads_readiness_rejects_unpinned_bd_binary(tmp_path: Path) -> None:
    repo, env = make_beads_repo(tmp_path)
    env["AEGIS_BD_SHA256"] = "0" * 64

    result = beads_readiness(repo, env)

    assert result.returncode == 2
    assert "configured bd executable SHA-256 does not match" in result.stdout


def test_beads_readiness_rejects_repo_local_task_authority_runtime(tmp_path: Path) -> None:
    repo, env = make_beads_repo(tmp_path)
    repo_runtime = repo / "tools" / "task_authority.py"
    write(repo_runtime, Path(task_authority.__file__).read_text(encoding="utf-8"))
    env["AEGIS_TASK_AUTHORITY_RUNTIME_FILE"] = str(repo_runtime)
    env["AEGIS_TASK_AUTHORITY_RUNTIME_SHA256"] = hashlib.sha256(
        repo_runtime.read_bytes()
    ).hexdigest()

    result = beads_readiness(repo, env)

    assert result.returncode == 2
    assert "outside the writable governed repository" in result.stdout


def test_beads_readiness_rejects_tampered_task_authority_runtime(tmp_path: Path) -> None:
    repo, env = make_beads_repo(tmp_path)
    runtime_path = Path(env["AEGIS_TASK_AUTHORITY_RUNTIME_FILE"])
    runtime_path.chmod(0o644)
    runtime_path.write_text("raise RuntimeError('tampered')\n", encoding="utf-8")

    result = beads_readiness(repo, env)

    assert result.returncode == 2
    assert "SHA-256 does not match its pinned digest" in result.stdout


def test_readiness_default_verbose_and_all_detail_modes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    default = readiness(repo)
    verbose = readiness(repo, "--verbose")
    complete = readiness(repo, "--all")

    assert default.returncode == verbose.returncode == complete.returncode == 0
    assert len(default.stdout.splitlines()) <= 60
    assert len(default.stdout.encode("utf-8")) <= 8 * 1024
    assert len(verbose.stdout.splitlines()) <= 120
    assert len(verbose.stdout.encode("utf-8")) <= 32 * 1024
    assert "Counts: total=" in default.stdout
    assert "Full stdout: rerun readiness.sh with --all." in default.stdout
    assert "Truncated:" not in complete.stdout
    assert complete.stdout.count("[ok]") > default.stdout.count("[ok]")


def test_ready_inside_linked_git_worktree(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    assert run(["git", "config", "user.email", "test@example.com"], repo).returncode == 0
    assert run(["git", "config", "user.name", "Test User"], repo).returncode == 0
    assert run(["git", "config", "commit.gpgsign", "false"], repo).returncode == 0
    assert run(["git", "add", "."], repo).returncode == 0
    assert run(["git", "commit", "-q", "-m", "init"], repo).returncode == 0
    worktree = tmp_path / "linked-worktree"
    assert run(["git", "worktree", "add", "-q", "-b", "feat/task-103-linked-worktree", str(worktree)], repo).returncode == 0

    result = readiness(worktree)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert (worktree / ".git").is_file()


def test_quick_mode_keeps_blocking_exit_code_and_concise_output(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "sessions" / "current").unlink()

    result = readiness(repo, "--quick")

    assert result.returncode == 2
    assert result.stdout.startswith("BLOCKED | task=103")
    assert "sessions/current symlink missing" in result.stdout
    assert "## Checks" not in result.stdout


def test_blocks_when_branch_has_no_task_id(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, branch="feature/claude-runtime-adapter")

    result = readiness(repo)

    assert result.returncode == 2
    assert "does not contain a task ID" in result.stdout


def test_blocks_when_taskmaster_parent_not_in_progress(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    tasks_path = repo / ".taskmaster" / "tasks" / "tasks.json"
    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    data["master"]["tasks"][0]["status"] = "pending"
    tasks_path.write_text(json.dumps(data), encoding="utf-8")

    result = readiness(repo)

    assert result.returncode == 2
    assert "expected 'in-progress'" in result.stdout


def test_aegis_current_work_is_authoritative_when_taskmaster_is_optional(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_aegis_current_work(repo, taskmaster_required=False)
    tasks_path = repo / ".taskmaster" / "tasks" / "tasks.json"
    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    data["master"]["tasks"][0]["status"] = "done"
    tasks_path.write_text(json.dumps(data), encoding="utf-8")

    result = readiness(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert "Aegis current work Task 103 is in-progress" in result.stdout
    assert "Taskmaster Task 103 is optional with status 'done'" in result.stdout


def test_aegis_current_work_can_require_taskmaster_alignment(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_aegis_current_work(repo, taskmaster_required=True)
    tasks_path = repo / ".taskmaster" / "tasks" / "tasks.json"
    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    data["master"]["tasks"][0]["status"] = "done"
    tasks_path.write_text(json.dumps(data), encoding="utf-8")

    result = readiness(repo)

    assert result.returncode == 2
    assert "Taskmaster Task 103 status is 'done', expected 'in-progress'" in result.stdout


def test_blocks_when_sessions_current_missing(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "sessions" / "current").unlink()

    result = readiness(repo)

    assert result.returncode == 2
    assert "sessions/current symlink missing" in result.stdout


def test_blocks_when_session_state_mismatches_symlink(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write(
        repo / "sessions" / "state.json",
        json.dumps({"current": "wrong-session.md", "paused": [], "updated_at": "2026-05-06T17:10:09+02:00"}),
    )

    result = readiness(repo)

    assert result.returncode == 2
    assert "sessions/state.json current is 'wrong-session.md'" in result.stdout


def test_blocks_when_plans_current_missing(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "plans" / "current").unlink()

    result = readiness(repo)

    assert result.returncode == 2
    assert "plans/current symlink missing" in result.stdout


def test_blocks_when_no_active_work_tracking_folder_exists(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    active_root = repo / "docs" / "ai" / "work-tracking" / "active"
    for child in active_root.iterdir():
        if child.is_dir():
            (child / "TRACKER.md").unlink()
            child.rmdir()

    result = readiness(repo)

    assert result.returncode == 2
    assert "expected exactly one ACTIVE work-tracking folder, found 0" in result.stdout


def test_blocks_when_active_folder_task_mismatches_branch(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    active_root = repo / "docs" / "ai" / "work-tracking" / "active"
    active = next(active_root.iterdir())
    active.rename(active_root / "20260506-task104-claude-runtime-adapter-ACTIVE")

    result = readiness(repo)

    assert result.returncode == 2
    assert "does not match Task 103" in result.stdout


def test_blocks_when_plan_and_tracker_checklists_diverge(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    tracker = next((repo / "docs" / "ai" / "work-tracking" / "active").iterdir()) / "TRACKER.md"
    text = tracker.read_text(encoding="utf-8").replace("[x] plan-step-scope", "[ ] plan-step-scope")
    tracker.write_text(text, encoding="utf-8")

    result = readiness(repo)

    assert result.returncode == 2
    assert "plan-step-scope mismatch" in result.stdout
