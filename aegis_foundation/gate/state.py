"""Read-only repository state primitives for workflow authorization."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Iterable



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


def bead_id_from_branch(branch: str) -> str | None:
    match = re.fullmatch(r"codex/([a-z][a-z0-9]*-[a-z0-9]+)(?:[-/].*)?", branch)
    return match.group(1) if match else None


def plan_bead_ids(plan_text: str) -> set[str]:
    values: list[str] = []
    for match in re.finditer(r"^bead_ids:\s*\[([^\]]*)\]\s*$", plan_text, flags=re.MULTILINE):
        values.extend(match.group(1).split(","))
    for match in re.finditer(r"^-\s+\*\*Bead IDs\*\*:\s*(.+?)\s*$", plan_text, flags=re.MULTILINE):
        values.extend(match.group(1).split(","))
    return {value.strip().strip("`'\"") for value in values if value.strip()}


def plan_branch_policies(plan_text: str) -> set[str]:
    values: list[str] = []
    for match in re.finditer(r"^branch_policy:\s*(\S+)\s*$", plan_text, flags=re.MULTILINE):
        values.append(match.group(1))
    for match in re.finditer(
        r"^-\s+\*\*Branch Policy\*\*:\s*(\S+)\s*$", plan_text, flags=re.MULTILINE
    ):
        values.append(match.group(1))
    return {value.strip().strip("`'\"") for value in values if value.strip()}


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
