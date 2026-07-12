#!/usr/bin/env bash
# Claude readiness gate.
# Read-only check used by Claude hooks before persistent mutations.

set -u

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


READY = "READY"
WARN = "WARN"
BLOCKED = "BLOCKED"


@dataclass
class Check:
    status: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether Claude workflow state is ready for persistent mutations."
    )
    parser.add_argument("--quick", action="store_true", help="Emit one machine-friendly status line.")
    parser.add_argument("--root", help="Repository root override for tests.")
    return parser.parse_args()


def run_git(root: Path, *args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def discover_root(root_arg: str | None) -> Path:
    if root_arg:
        return Path(root_arg).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def task_id_from_branch(branch: str) -> str | None:
    match = re.search(r"(?:^|[-_/])task-?(\d+)(?:[-_/]|$)", branch)
    if match:
        return match.group(1)
    return None


def text_references_task(text: str, task_id: str) -> bool:
    patterns = [
        rf"\bTaskmaster\s+Task\s+{re.escape(task_id)}\b",
        rf"\bTask\s+{re.escape(task_id)}\b",
        rf"\btask{re.escape(task_id)}\b",
        rf"\btask-{re.escape(task_id)}\b",
        rf"task_ids:\s*\[[^\]]*\b{re.escape(task_id)}\b[^\]]*\]",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def text_references_work(text: str, work_id: str) -> bool:
    return bool(work_id and re.search(rf"\b{re.escape(work_id)}\b", text, flags=re.IGNORECASE))


def taskmaster_tasks_payload(data: object) -> tuple[str, list[dict[str, object]]] | None:
    if not isinstance(data, dict):
        return None
    state = data.get("master")
    if isinstance(state, dict) and isinstance(state.get("tasks"), list):
        return "master", state["tasks"]  # type: ignore[return-value]
    if isinstance(data.get("tasks"), list):
        return "default", data["tasks"]  # type: ignore[return-value]
    for tag, value in data.items():
        if isinstance(value, dict) and isinstance(value.get("tasks"), list):
            return str(tag), value["tasks"]  # type: ignore[return-value]
    return None


def find_task(tasks: Iterable[dict[str, object]], task_id: str) -> dict[str, object] | None:
    for task in tasks:
        if str(task.get("id")) == task_id:
            return task
    return None


def aegis_work_task(data: object) -> dict[str, object] | None:
    if not isinstance(data, dict):
        return None
    task = data.get("task")
    return task if isinstance(task, dict) else None


def aegis_work_mode(data: object) -> str:
    if not isinstance(data, dict):
        return ""
    return str(data.get("mode") or "task")


def aegis_integration_required(data: object, name: str) -> bool:
    if not isinstance(data, dict):
        return False
    integrations = data.get("integrations")
    if not isinstance(integrations, dict):
        return False
    integration = integrations.get(name)
    return isinstance(integration, dict) and integration.get("required") is True


def symlink_target(path: Path) -> tuple[Path | None, str | None]:
    if not path.exists() and not path.is_symlink():
        return None, None
    if not path.is_symlink():
        return None, None
    raw_target = path.readlink()
    if raw_target.is_absolute():
        return raw_target, raw_target.as_posix()
    return (path.parent / raw_target).resolve(), raw_target.as_posix()


def parse_plan_statuses(plan_text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in plan_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        step_id = cells[0]
        if not step_id.startswith("plan-step-"):
            continue
        statuses[step_id] = cells[-1].lower()
    return statuses


def parse_tracker_statuses(tracker_text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in tracker_text.splitlines():
        match = re.match(r"- \[([ xX])\]\s+(plan-step-[a-z0-9-]+)\b", line)
        if not match:
            continue
        statuses[match.group(2)] = "completed" if match.group(1).lower() == "x" else "pending"
    return statuses


def expected_tracker_status(plan_status: str) -> str | None:
    if plan_status == "completed":
        return "completed"
    if plan_status in {"pending", "in-progress"}:
        return "pending"
    return None


def check_plan_tracker_alignment(plan_text: str, tracker_text: str) -> list[str]:
    issues: list[str] = []
    plan_statuses = parse_plan_statuses(plan_text)
    tracker_statuses = parse_tracker_statuses(tracker_text)
    required_steps = ["plan-step-scope", "plan-step-implement", "plan-step-verify"]

    for step in required_steps:
        if step not in plan_statuses:
            issues.append(f"plan missing {step}")
            continue
        if step not in tracker_statuses:
            issues.append(f"tracker missing {step}")
            continue
        expected = expected_tracker_status(plan_statuses[step])
        if expected and tracker_statuses[step] != expected:
            issues.append(
                f"{step} mismatch: plan is {plan_statuses[step]}, tracker is {tracker_statuses[step]}"
            )
    return issues


def check_taskmaster_task(root: Path, task_id: str, *, required: bool, checks: list[Check]) -> None:
    tasks_path = root / ".taskmaster" / "tasks" / "tasks.json"
    if not tasks_path.is_file():
        if required:
            checks.append(Check(BLOCKED, "Taskmaster is required by Aegis current work but tasks file is missing"))
        return

    try:
        payload = taskmaster_tasks_payload(read_json(tasks_path))
    except Exception as exc:  # noqa: BLE001 - surface exact readiness failure.
        if required:
            checks.append(Check(BLOCKED, f"could not read required Taskmaster tasks: {exc}"))
        else:
            checks.append(Check(READY, f"Taskmaster present but optional and unreadable: {exc}"))
        return

    if payload is None:
        if required:
            checks.append(Check(BLOCKED, "required Taskmaster tasks JSON has an unsupported shape"))
        else:
            checks.append(Check(READY, "Taskmaster present but optional and has unsupported shape"))
        return

    tag, tasks = payload
    task = find_task(tasks, task_id)
    if not task:
        if required:
            checks.append(Check(BLOCKED, f"required Taskmaster Task {task_id} missing from tag '{tag}'"))
        else:
            checks.append(Check(READY, f"Taskmaster present but optional; Task {task_id} not found in tag '{tag}'"))
        return

    status = task.get("status")
    if status != "in-progress":
        if required:
            checks.append(Check(BLOCKED, f"Taskmaster Task {task_id} status is {status!r}, expected 'in-progress'"))
        else:
            checks.append(Check(READY, f"Taskmaster Task {task_id} is optional with status {status!r}"))
        return

    prefix = "Required Taskmaster" if required else "Optional Taskmaster"
    checks.append(Check(READY, f"{prefix} Task {task_id} is in-progress"))


def load_source_workflow_state(root: Path):
    """Load the source-only resolver only from an uninstalled Aegis source tree."""

    if (root / ".aegis" / "foundation-manifest.json").exists():
        return None
    if (root / ".aegis" / "state" / "current-work.json").exists():
        return None
    markers = (
        root / "schemas" / "aegis" / "foundation-manifest.schema.json",
        root / "scripts" / "_aegis_installer.py",
        root / ".claude" / "scripts" / "readiness.sh",
        root / "aegis_foundation" / "assets" / ".claude" / "scripts" / "readiness.sh",
        root / "aegis_foundation" / "assets" / "scripts" / "codex-guard",
    )
    if not all(path.is_file() for path in markers):
        return None
    try:
        pyproject_text = read_text(root / "pyproject.toml")
    except OSError:
        return None
    if not re.search(r'^name\s*=\s*["\']aegis-foundation["\']\s*$', pyproject_text, re.MULTILINE):
        return None

    helper_path = root / "scripts" / "_source_workflow_state.py"
    if not helper_path.is_file():
        return None
    module_name = "_aegis_source_workflow_state_runtime"
    spec = importlib.util.spec_from_file_location(module_name, helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load source workflow helper: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def build_completed_source_checks(
    root: Path,
    task_id: str,
    source_work: object,
    checks: list[Check],
) -> tuple[str | None, list[Check]]:
    tracker_path = Path(getattr(source_work, "tracker_path"))
    archive_folder = Path(getattr(source_work, "archive_folder"))
    checks.append(Check(READY, f"Taskmaster Task {task_id} is done for derived source closeout"))
    checks.append(
        Check(
            READY,
            f"completed source tracker derived from {archive_folder.relative_to(root).as_posix()}",
        )
    )

    session_current = root / "sessions" / "current"
    session_path, session_target = symlink_target(session_current)
    if session_path is None or session_target is None:
        checks.append(Check(BLOCKED, "sessions/current symlink missing"))
    elif not session_path.is_file():
        checks.append(Check(BLOCKED, f"sessions/current points to missing file: {session_target}"))
    else:
        session_text = read_text(session_path)
        if not text_references_task(session_text, task_id):
            checks.append(Check(BLOCKED, f"current session does not reference completed Task {task_id}"))
        else:
            checks.append(Check(READY, f"current session references completed Task {task_id}"))

        state_path = root / "sessions" / "state.json"
        if not state_path.is_file():
            checks.append(Check(BLOCKED, "sessions/state.json missing"))
        else:
            try:
                state = read_json(state_path)
            except Exception as exc:  # noqa: BLE001 - surface exact readiness failure.
                checks.append(Check(BLOCKED, f"sessions/state.json invalid: {exc}"))
            else:
                current_value = state.get("current") if isinstance(state, dict) else None
                if current_value != session_path.name:
                    checks.append(
                        Check(
                            BLOCKED,
                            f"sessions/state.json current is {current_value!r}, expected {session_path.name!r}",
                        )
                    )
                else:
                    checks.append(Check(READY, "sessions/state.json current matches sessions/current"))

    plan_current = root / "plans" / "current"
    plan_path, plan_target = symlink_target(plan_current)
    plan_text: str | None = None
    if plan_path is None or plan_target is None:
        checks.append(Check(BLOCKED, "plans/current symlink missing"))
    elif not plan_path.is_file():
        checks.append(Check(BLOCKED, f"plans/current points to missing file: {plan_target}"))
    else:
        plan_text = read_text(plan_path)
        if not text_references_task(plan_text, task_id):
            checks.append(Check(BLOCKED, f"current plan does not reference completed Task {task_id}"))
        else:
            checks.append(Check(READY, f"current plan references completed Task {task_id}"))

    tracker_text = read_text(tracker_path)
    checks.append(Check(READY, f"completed tracker references Task {task_id}"))
    if plan_text is not None:
        alignment_issues = check_plan_tracker_alignment(plan_text, tracker_text)
        plan_statuses = parse_plan_statuses(plan_text)
        tracker_statuses = parse_tracker_statuses(tracker_text)
        for step in ("plan-step-scope", "plan-step-implement", "plan-step-verify"):
            if plan_statuses.get(step) != "completed":
                alignment_issues.append(f"completed source plan has {step}={plan_statuses.get(step)!r}")
            if tracker_statuses.get(step) != "completed":
                alignment_issues.append(f"completed source tracker has {step}={tracker_statuses.get(step)!r}")
        if alignment_issues:
            for issue in alignment_issues:
                checks.append(Check(BLOCKED, f"completed plan/tracker alignment failure: {issue}"))
        else:
            checks.append(Check(READY, "completed plan and tracker steps align"))

    return task_id, checks


def build_observation_checks(root: Path, branch: str, aegis_work: object) -> tuple[str | None, list[Check]]:
    checks: list[Check] = []
    task = aegis_work_task(aegis_work)
    paths = aegis_work.get("paths") if isinstance(aegis_work, dict) and isinstance(aegis_work.get("paths"), dict) else {}
    work_id = str(task.get("id") if task else "").strip()
    slug = str(task.get("slug") if task else "").strip()
    status = str(aegis_work.get("status") if isinstance(aegis_work, dict) else "").strip()

    if not task or not work_id or not slug or status != "in-progress":
        checks.append(Check(BLOCKED, "observation current work is missing id, slug, or in-progress status"))
        return work_id or None, checks

    checks.append(Check(READY, f"branch '{branch}' is accepted for observation mode without a task ID"))
    checks.append(Check(READY, f"Aegis observation {work_id} is in-progress"))

    session_rel = str(paths.get("session") or "").strip()
    plan_rel = str(paths.get("plan") or "").strip()
    work_rel = str(paths.get("work_tracking") or "").strip()
    if not session_rel or not plan_rel or not work_rel:
        checks.append(Check(BLOCKED, "observation current work paths are incomplete"))
        return work_id, checks

    session_current = root / "sessions" / "current"
    session_path, session_target = symlink_target(session_current)
    if session_path is None or session_target is None:
        checks.append(Check(BLOCKED, "sessions/current symlink missing"))
    elif session_path.relative_to(root).as_posix() != session_rel:
        checks.append(Check(BLOCKED, f"sessions/current does not point to observation session {session_rel}"))
    elif not session_path.is_file():
        checks.append(Check(BLOCKED, f"sessions/current points to missing file: {session_target}"))
    else:
        session_text = read_text(session_path)
        if not text_references_work(session_text, work_id):
            checks.append(Check(BLOCKED, f"active session does not reference observation {work_id}"))
        else:
            checks.append(Check(READY, f"active session references observation {work_id}"))

    plan_current = root / "plans" / "current"
    plan_path, plan_target = symlink_target(plan_current)
    plan_text: str | None = None
    if plan_path is None or plan_target is None:
        checks.append(Check(BLOCKED, "plans/current symlink missing"))
    elif plan_path.relative_to(root).as_posix() != plan_rel:
        checks.append(Check(BLOCKED, f"plans/current does not point to observation plan {plan_rel}"))
    elif not plan_path.is_file():
        checks.append(Check(BLOCKED, f"plans/current points to missing file: {plan_target}"))
    else:
        plan_text = read_text(plan_path)
        if not text_references_work(plan_text, work_id):
            checks.append(Check(BLOCKED, f"active plan does not reference observation {work_id}"))
        else:
            checks.append(Check(READY, f"active plan references observation {work_id}"))

    tracker_path = root / work_rel / "TRACKER.md"
    tracker_text: str | None = None
    if not (root / work_rel).is_dir():
        checks.append(Check(BLOCKED, f"observation work-tracking folder missing: {work_rel}"))
    elif not tracker_path.is_file():
        checks.append(Check(BLOCKED, f"{tracker_path.relative_to(root)} missing"))
    else:
        tracker_text = read_text(tracker_path)
        if not text_references_work(tracker_text, work_id):
            checks.append(Check(BLOCKED, f"active tracker does not reference observation {work_id}"))
        else:
            checks.append(Check(READY, f"active tracker references observation {work_id}"))

    if plan_text is not None and tracker_text is not None:
        alignment_issues = check_plan_tracker_alignment(plan_text, tracker_text)
        if alignment_issues:
            for issue in alignment_issues:
                checks.append(Check(BLOCKED, f"plan/tracker alignment failure: {issue}"))
        else:
            checks.append(Check(READY, "plan-step statuses align between plan and tracker"))

    return work_id, checks


def build_checks(root: Path) -> tuple[str | None, list[Check]]:
    checks: list[Check] = []

    code, inside_work_tree, err = run_git(root, "rev-parse", "--is-inside-work-tree")
    if code != 0 or inside_work_tree != "true":
        checks.append(Check(BLOCKED, f"{root} is not a git work tree: {err or inside_work_tree or 'unknown'}"))
        return None, checks

    code, branch, err = run_git(root, "branch", "--show-current")
    if code != 0 or not branch:
        checks.append(Check(BLOCKED, f"could not determine current git branch: {err or 'empty branch'}"))
        return None, checks

    aegis_work_path = root / ".aegis" / "state" / "current-work.json"
    aegis_work: object | None = None
    ignore_current_work_for_readiness = False
    if aegis_work_path.is_file():
        try:
            aegis_work = read_json(aegis_work_path)
        except Exception as exc:  # noqa: BLE001 - surface exact readiness failure.
            checks.append(Check(BLOCKED, f"could not read Aegis current work state: {exc}"))
            return None, checks
        if aegis_work_mode(aegis_work) == "observation":
            status = str(aegis_work.get("status") if isinstance(aegis_work, dict) else "").strip()
            if status == "in-progress":
                return build_observation_checks(root, branch, aegis_work)
            if status == "completed":
                task = aegis_work_task(aegis_work)
                work_id = str(task.get("id") if task else "").strip()
                checks.append(Check(READY, f"Aegis observation {work_id or '<unknown>'} is completed"))
                ignore_current_work_for_readiness = True
            else:
                checks.append(Check(BLOCKED, f"Aegis observation status is {status!r}, expected 'in-progress' or 'completed'"))
                return None, checks

    task_id = task_id_from_branch(branch)
    if not task_id:
        checks.append(Check(BLOCKED, f"branch '{branch}' does not contain a task ID"))
        return None, checks
    checks.append(Check(READY, f"branch '{branch}' maps to Task {task_id}"))

    if not aegis_work_path.is_file():
        try:
            source_module = load_source_workflow_state(root)
            source_work = (
                source_module.derive_completed_source_work(root, branch)
                if source_module is not None
                else None
            )
        except Exception as exc:  # noqa: BLE001 - source contradictions fail closed.
            checks.append(Check(BLOCKED, f"source closeout derivation failed: {exc}"))
            return task_id, checks
        if source_work is not None:
            return build_completed_source_checks(root, task_id, source_work, checks)

    if aegis_work_path.is_file() and not ignore_current_work_for_readiness:
        try:
            aegis_work = aegis_work if aegis_work is not None else read_json(aegis_work_path)
            task = aegis_work_task(aegis_work)
        except Exception as exc:  # noqa: BLE001 - surface exact readiness failure.
            checks.append(Check(BLOCKED, f"could not read Aegis current work state: {exc}"))
        else:
            if task is None:
                checks.append(Check(BLOCKED, "Aegis current work state has an unsupported shape"))
            elif str(task.get("id")) != task_id:
                checks.append(Check(BLOCKED, f"Aegis current work task is {task.get('id')!r}, expected Task {task_id}"))
            elif task.get("status") != "in-progress":
                checks.append(
                    Check(BLOCKED, f"Aegis current work status is {task.get('status')!r}, expected 'in-progress'")
                )
            else:
                checks.append(Check(READY, f"Aegis current work Task {task_id} is in-progress"))
                check_taskmaster_task(
                    root,
                    task_id,
                    required=aegis_integration_required(aegis_work, "taskmaster"),
                    checks=checks,
                )
    elif (root / ".taskmaster" / "tasks" / "tasks.json").is_file():
        check_taskmaster_task(root, task_id, required=True, checks=checks)
    else:
        checks.append(Check(BLOCKED, "no Taskmaster tasks file or Aegis current work state found"))

    session_current = root / "sessions" / "current"
    session_path, session_target = symlink_target(session_current)
    if session_path is None or session_target is None:
        checks.append(Check(BLOCKED, "sessions/current symlink missing"))
    elif not session_path.is_file():
        checks.append(Check(BLOCKED, f"sessions/current points to missing file: {session_target}"))
    else:
        session_text = read_text(session_path)
        if not text_references_task(session_text, task_id):
            checks.append(Check(BLOCKED, f"active session does not reference Task {task_id}"))
        else:
            checks.append(Check(READY, f"active session references Task {task_id}"))

        state_path = root / "sessions" / "state.json"
        if not state_path.is_file():
            checks.append(Check(BLOCKED, "sessions/state.json missing"))
        else:
            try:
                state = read_json(state_path)
            except Exception as exc:  # noqa: BLE001 - surface exact readiness failure.
                checks.append(Check(BLOCKED, f"sessions/state.json invalid: {exc}"))
            else:
                current_value = state.get("current") if isinstance(state, dict) else None
                if current_value != session_path.name:
                    checks.append(
                        Check(
                            BLOCKED,
                            f"sessions/state.json current is {current_value!r}, expected {session_path.name!r}",
                        )
                    )
                else:
                    checks.append(Check(READY, "sessions/state.json current matches sessions/current"))

    plan_current = root / "plans" / "current"
    plan_path, plan_target = symlink_target(plan_current)
    plan_text: str | None = None
    if plan_path is None or plan_target is None:
        checks.append(Check(BLOCKED, "plans/current symlink missing"))
    elif not plan_path.is_file():
        checks.append(Check(BLOCKED, f"plans/current points to missing file: {plan_target}"))
    else:
        plan_text = read_text(plan_path)
        if not text_references_task(plan_text, task_id):
            checks.append(Check(BLOCKED, f"active plan does not reference Task {task_id}"))
        else:
            checks.append(Check(READY, f"active plan references Task {task_id}"))

    active_root = root / "docs" / "ai" / "work-tracking" / "active"
    tracker_text: str | None = None
    if not active_root.is_dir():
        checks.append(Check(BLOCKED, "active work-tracking root missing"))
    else:
        active_folders = sorted(path for path in active_root.iterdir() if path.is_dir() and path.name.endswith("-ACTIVE"))
        if len(active_folders) != 1:
            checks.append(Check(BLOCKED, f"expected exactly one ACTIVE work-tracking folder, found {len(active_folders)}"))
        else:
            active_folder = active_folders[0]
            if not re.search(rf"(?:^|[-_])task-?{re.escape(task_id)}(?:[-_]|$)", active_folder.name):
                checks.append(Check(BLOCKED, f"ACTIVE folder '{active_folder.name}' does not match Task {task_id}"))
            else:
                checks.append(Check(READY, f"ACTIVE folder '{active_folder.name}' matches Task {task_id}"))

            tracker_path = active_folder / "TRACKER.md"
            if not tracker_path.is_file():
                checks.append(Check(BLOCKED, f"{tracker_path.relative_to(root)} missing"))
            else:
                tracker_text = read_text(tracker_path)
                if not text_references_task(tracker_text, task_id):
                    checks.append(Check(BLOCKED, f"active tracker does not reference Task {task_id}"))
                else:
                    checks.append(Check(READY, f"active tracker references Task {task_id}"))

    if plan_text is not None and tracker_text is not None:
        alignment_issues = check_plan_tracker_alignment(plan_text, tracker_text)
        if alignment_issues:
            for issue in alignment_issues:
                checks.append(Check(BLOCKED, f"plan/tracker alignment failure: {issue}"))
        else:
            checks.append(Check(READY, "plan-step statuses align between plan and tracker"))

    return task_id, checks


def summarize_state(checks: list[Check]) -> str:
    if any(check.status == BLOCKED for check in checks):
        return BLOCKED
    if any(check.status == WARN for check in checks):
        return WARN
    return READY


def print_quick(state: str, task_id: str | None, checks: list[Check]) -> None:
    blocked = [check.message for check in checks if check.status == BLOCKED]
    warnings = [check.message for check in checks if check.status == WARN]
    parts = [state]
    if task_id:
        parts.append(f"task={task_id}")
    if blocked:
        parts.append(f"blocked={len(blocked)}")
        parts.append(f"first={blocked[0]}")
    elif warnings:
        parts.append(f"warnings={len(warnings)}")
        parts.append(f"first={warnings[0]}")
    print(" | ".join(parts))


def print_full(root: Path, state: str, task_id: str | None, checks: list[Check]) -> None:
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z %z")
    print(f"# CLAUDE READINESS - {now}")
    print(f"STATE: {state}")
    print(f"TASK: {task_id or 'unknown'}")
    print(f"ROOT: {root}")
    print()
    print("## Checks")
    prefixes = {READY: "[ok]", WARN: "[warn]", BLOCKED: "[blocked]"}
    for check in checks:
        print(f"{prefixes[check.status]} {check.message}")

    if state == BLOCKED:
        print()
        print("## Remediation")
        print("- Start or repair the workflow before Claude performs persistent mutations.")
        print("- Required state: task branch, Aegis current work or Taskmaster in-progress task, sessions/current, plans/current, and one ACTIVE tracker for the same task.")
        print("- Use `aegis kickoff --task <id> --slug <slug> --title \"<title>\"` or the project kickoff workflow instead of writing files or memory by hand.")


def main() -> int:
    args = parse_args()
    root = discover_root(args.root)
    task_id, checks = build_checks(root)
    state = summarize_state(checks)
    if args.quick:
        print_quick(state, task_id, checks)
    else:
        print_full(root, state, task_id, checks)
    return 2 if state == BLOCKED else 0


if __name__ == "__main__":
    sys.exit(main())
PY
