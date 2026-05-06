#!/usr/bin/env bash
# Claude readiness gate.
# Read-only check used by Claude hooks before persistent mutations.

set -u

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
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

    task_id = task_id_from_branch(branch)
    if not task_id:
        checks.append(Check(BLOCKED, f"branch '{branch}' does not contain a task ID"))
        return None, checks
    checks.append(Check(READY, f"branch '{branch}' maps to Task {task_id}"))

    tasks_path = root / ".taskmaster" / "tasks" / "tasks.json"
    if not tasks_path.is_file():
        checks.append(Check(BLOCKED, ".taskmaster/tasks/tasks.json missing"))
    else:
        try:
            payload = taskmaster_tasks_payload(read_json(tasks_path))
        except Exception as exc:  # noqa: BLE001 - surface exact readiness failure.
            checks.append(Check(BLOCKED, f"could not read Taskmaster tasks: {exc}"))
        else:
            if payload is None:
                checks.append(Check(BLOCKED, "Taskmaster tasks JSON has an unsupported shape"))
            else:
                tag, tasks = payload
                task = find_task(tasks, task_id)
                if not task:
                    checks.append(Check(BLOCKED, f"Taskmaster Task {task_id} missing from tag '{tag}'"))
                elif task.get("status") != "in-progress":
                    checks.append(
                        Check(BLOCKED, f"Taskmaster Task {task_id} status is {task.get('status')!r}, expected 'in-progress'")
                    )
                else:
                    checks.append(Check(READY, f"Taskmaster Task {task_id} is in-progress"))

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
        print("- Required state: task branch, Taskmaster in-progress task, sessions/current, plans/current, and one ACTIVE tracker for the same task.")
        print("- Use the project kickoff workflow instead of writing files or memory by hand.")


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
