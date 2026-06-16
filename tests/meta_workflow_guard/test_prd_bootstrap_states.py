"""TM 190: fresh-project PRD bootstrap states in aegis next.

A brand-new project starts with no Taskmaster ledger, then an empty ledger, then (optionally) a
PRD, then parsed-but-unstarted tasks, then a first task ready to kick off. next_action must
guide that whole bootstrap with read-only detection, separate setup/planning mutations from
product implementation, and NEVER bind a fabricated task id before the ledger exists. These
tests walk a temporary brand-new repo through every state and lock the boundaries.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import _aegis_installer as inst  # noqa: E402
from scripts._aegis_installer import install, next_action  # noqa: E402

REAL_PRD = (
    "# BrandMark PRD\n\n<context>\n"
    "BrandMark is a tool for managing brand assets across teams. This document captures the\n"
    "real product requirements: asset ingestion, versioning, approval flows, and export.\n"
    "</context>\n\n<PRD>\n"
    "## Features\n- Asset library with version history\n- Approval workflow\n- Export presets\n"
    "</PRD>\n"
)


def _fresh(tmp_path: Path, *, name: str, taskmaster: object | None = None,
           prd: str | None = None, prd_name: str = "prd.txt", extra_docs: dict[str, str] | None = None) -> Path:
    target = tmp_path / name
    target.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)
    if taskmaster is not None:
        tasks_path = target / ".taskmaster" / "tasks" / "tasks.json"
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.write_text(
            taskmaster if isinstance(taskmaster, str) else json.dumps(taskmaster),
            encoding="utf-8",
        )
    if prd is not None:
        prd_path = target / ".taskmaster" / "docs" / prd_name
        prd_path.parent.mkdir(parents=True, exist_ok=True)
        prd_path.write_text(prd, encoding="utf-8")
    for rel, text in (extra_docs or {}).items():
        doc = target / ".taskmaster" / "docs" / rel
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text(text, encoding="utf-8")
    install(target, source_root=REPO_ROOT, primary_agent="codex", agents=["codex"], apply=True)
    reload_marker = target / ".aegis" / "state" / "client-reload-required.json"
    if reload_marker.exists():
        reload_marker.unlink()
    return target


def _state(target: Path) -> dict:
    return next_action(target, source_root=REPO_ROOT)


def test_no_taskmaster(tmp_path: Path) -> None:
    guided = _state(_fresh(tmp_path, name="no-tm"))
    assert guided["state"] == "no_taskmaster"
    # preserves the local-work path AND offers the task-driven path
    assert guided["suggested_mcp_call"]["tool"] == "aegis.start"
    repairs = "\n".join(guided["copyable_repairs"])
    assert "aegis start" in repairs and "task-master init" in repairs
    assert guided["continuation_brief"]["next_safe_action"] == "init_taskmaster_or_start_local"
    _assert_no_bound_task_id(guided)


def test_taskmaster_empty_without_prd(tmp_path: Path) -> None:
    guided = _state(_fresh(tmp_path, name="tm-empty", taskmaster={"master": {"tasks": []}}))
    assert guided["state"] == "taskmaster_empty"  # NOT installed_taskmaster_invalid
    assert "add-task" in guided["suggested_cli"] or "add-task" in "\n".join(guided["copyable_repairs"])
    _assert_no_bound_task_id(guided)


def test_prd_available_not_parsed(tmp_path: Path) -> None:
    guided = _state(_fresh(tmp_path, name="prd-ready", taskmaster={"master": {"tasks": []}}, prd=REAL_PRD))
    assert guided["state"] == "prd_available_not_parsed"
    assert "parse-prd" in guided["suggested_cli"]
    assert ".taskmaster/docs/prd.txt" in guided["suggested_cli"]
    # parse-prd is only SUGGESTED behind explicit approval, never auto-run.
    boundary = " ".join(guided["continuation_brief"]["confirmation_boundary"]).lower()
    assert "parse-prd" in boundary and ("approval" in boundary or "explicit" in boundary)
    _assert_no_bound_task_id(guided)


def test_example_template_is_not_a_real_prd(tmp_path: Path) -> None:
    # Copying the shipped example_prd.txt to docs/prd.txt must NOT read as an available PRD.
    template = REPO_ROOT / ".taskmaster" / "templates" / "example_prd.txt"
    example = template.read_text(encoding="utf-8") if template.is_file() else (
        "[Provide a high-level overview of your product here]\n"
    )
    guided = _state(_fresh(tmp_path, name="example-prd", taskmaster={"master": {"tasks": []}}, prd=example))
    assert guided["state"] == "taskmaster_empty"


def test_non_canonical_doc_is_not_a_prd(tmp_path: Path) -> None:
    # A non-PRD markdown doc under docs/ must not false-positive as an available PRD.
    guided = _state(_fresh(
        tmp_path, name="other-doc", taskmaster={"master": {"tasks": []}},
        extra_docs={"reconcile-enablement-gate-backlog-amendment.md": "# Amendment\nUnrelated.\n"},
    ))
    assert guided["state"] == "taskmaster_empty"


def test_whitespace_only_prd_is_not_available(tmp_path: Path) -> None:
    guided = _state(_fresh(tmp_path, name="ws-prd", taskmaster={"master": {"tasks": []}}, prd="   \n\t\n"))
    assert guided["state"] == "taskmaster_empty"


def test_first_task_ready_without_prd(tmp_path: Path) -> None:
    guided = _state(_fresh(
        tmp_path, name="first-ready",
        taskmaster={"master": {"tasks": [{"id": 1, "title": "A", "status": "pending"}]}},
    ))
    assert guided["state"] == "first_task_ready"
    repairs = "\n".join(guided["copyable_repairs"])
    assert "task-master next" in repairs and "aegis kickoff" in repairs
    assert "observe start" in repairs
    # the kickoff uses a placeholder, never a fabricated bound id
    assert "--task <id>" in repairs and "--task 1" not in repairs


def test_prd_parsed_tasks_pending(tmp_path: Path) -> None:
    guided = _state(_fresh(
        tmp_path, name="parsed-pending",
        taskmaster={"master": {"tasks": [{"id": 1, "title": "A", "status": "pending"}]}},
        prd=REAL_PRD,
    ))
    assert guided["state"] == "prd_parsed_tasks_pending"
    repairs = "\n".join(guided["copyable_repairs"])
    assert "task-master list --status=pending" in repairs
    assert "--task 1" not in repairs


def test_in_progress_task_is_installed_taskmaster_present(tmp_path: Path) -> None:
    # Regression: once a task is started, the existing terminal state is unchanged.
    guided = _state(_fresh(
        tmp_path, name="in-progress",
        taskmaster={"master": {"tasks": [{"id": 1, "title": "A", "status": "in-progress"}]}},
        prd=REAL_PRD,
    ))
    assert guided["state"] == "installed_taskmaster_present"


def test_corrupt_ledger_still_invalid(tmp_path: Path) -> None:
    # Regression: genuine corruption still routes to repair, not a bootstrap state.
    guided = _state(_fresh(tmp_path, name="corrupt", taskmaster="{not json"))
    assert guided["state"] == "installed_taskmaster_invalid"


def test_bootstrap_detection_is_read_only(tmp_path: Path) -> None:
    target = _fresh(tmp_path, name="ro", taskmaster={"master": {"tasks": []}}, prd=REAL_PRD)
    tasks_before = (target / ".taskmaster" / "tasks" / "tasks.json").read_text(encoding="utf-8")
    prd_before = (target / ".taskmaster" / "docs" / "prd.txt").read_text(encoding="utf-8")
    guided = _state(target)
    assert guided["read_only"] is True
    # detection must not parse the PRD or mutate the ledger
    assert (target / ".taskmaster" / "tasks" / "tasks.json").read_text(encoding="utf-8") == tasks_before
    assert (target / ".taskmaster" / "docs" / "prd.txt").read_text(encoding="utf-8") == prd_before


def test_all_five_states_have_briefs() -> None:
    for state in (
        "no_taskmaster", "taskmaster_empty", "prd_available_not_parsed",
        "prd_parsed_tasks_pending", "first_task_ready",
    ):
        assert state in inst.CONTINUATION_BRIEF_BY_STATE, state
        brief = inst._continuation_brief(state, "start")
        assert brief["read_only"] is True
        assert brief["continue_means"].strip()


def _assert_no_bound_task_id(guided: dict) -> None:
    # Pre-ledger states must never emit a concrete bound numeric task id (only <id> placeholders):
    # no bound task object, and no `--task <number>` anywhere in the payload.
    haystack = json.dumps(guided)
    assert '"task":' not in haystack, f"pre-ledger payload bound a task object: {haystack}"
    assert not re.search(r"--task\s+\d+", haystack), f"pre-ledger payload bound a numeric task id: {haystack}"
