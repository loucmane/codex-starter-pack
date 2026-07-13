"""TM 225: next_action surfaces doctor-derived repair states (residual #2 of TM 189).

When an installed workflow has fixable drift, `aegis next` should route a bare "continue" to
the correct repair lane BEFORE the scope/implement/verify/closeout ladder:
- safe_repair_available — drift that `aegis repair --apply` can fix (show plan, then apply safe).
- manual_review_repair — drift that needs human resolution; never auto-applied.

These tests lock the two states, their correct classification, the precedence rules (pending
tracking outranks repair; repair outranks the plan ladder; a healthy task never trips a repair
state), read-only-ness, and that detection does not recurse through doctor().
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import _aegis_installer as inst  # noqa: E402
from scripts._aegis_installer import (  # noqa: E402
    AEGIS_LOCAL_BIN_REL,
    AEGIS_PENDING_TRACKING_REL,
    doctor,
    install,
    kickoff,
    next_action,
)
from tests.meta_workflow_guard.test_aegis_installer import (  # noqa: E402
    simulate_codex_reload,
)


def _kickoff_target(tmp_path: Path) -> Path:
    target = tmp_path / "repair-states"
    target.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)
    (target / "src").mkdir()
    (target / "src" / "main.ts").write_text("export const ready = true;\n", encoding="utf-8")
    install(target, source_root=REPO_ROOT, primary_agent="codex", agents=["codex"], apply=True)
    simulate_codex_reload(target)
    kickoff(target, task_id="42", slug="task-42-x", title="X", source_root=REPO_ROOT)
    return target


def _induce_safe_drift(target: Path) -> None:
    # Deleting a manifest-managed file yields a `restore_managed_file` (safe) repair action.
    (target / AEGIS_LOCAL_BIN_REL).unlink()


def _induce_manual_drift(target: Path) -> None:
    # The only producer of a non-safe action today: a managed FILE path replaced by a DIRECTORY.
    managed = target / AEGIS_LOCAL_BIN_REL
    managed.unlink()
    managed.mkdir()


def test_clean_task_never_trips_a_repair_state(tmp_path: Path) -> None:
    # The load-bearing no-false-positive guard: a healthy kickoff still emits a cosmetic
    # normalize_plan_table action, which must NOT route to a repair state.
    target = _kickoff_target(tmp_path)
    state = next_action(target, source_root=REPO_ROOT)["state"]
    assert state == "scope_required", state


def test_missing_managed_file_is_safe_repair_available(tmp_path: Path) -> None:
    target = _kickoff_target(tmp_path)
    _induce_safe_drift(target)
    guided = next_action(target, source_root=REPO_ROOT)
    assert guided["state"] == "safe_repair_available"
    assert guided["phase"] == "repair"
    assert guided["suggested_mcp_call"]["tool"] == "aegis.doctor"
    assert "aegis repair --target-dir . --apply" in "\n".join(guided["copyable_repairs"])
    plan = guided["details"]["repair_plan"]
    assert plan["available"] is True and plan["safe"] >= 1
    assert plan["apply_command"] == "aegis repair --apply"
    # The brief routes "continue" to the apply-after-review lane.
    assert guided["continuation_brief"]["next_safe_action"] == "review_repair_plan_then_apply_safe"


def test_managed_path_as_directory_is_manual_review_repair(tmp_path: Path) -> None:
    target = _kickoff_target(tmp_path)
    _induce_manual_drift(target)
    guided = next_action(target, source_root=REPO_ROOT)
    assert guided["state"] == "manual_review_repair"
    assert guided["phase"] == "repair"
    plan = guided["details"]["repair_plan"]
    assert plan["safe"] == 0 and plan["manual_review"] >= 1
    assert plan["apply_command"] is None
    # Manual review must NOT advertise an --apply path.
    assert "repair --target-dir . --apply" not in "\n".join(guided["copyable_repairs"])
    assert guided["continuation_brief"]["next_safe_action"] == "surface_repair_plan_for_review"


def test_pending_tracking_outranks_repair(tmp_path: Path) -> None:
    # The one invariant above repair: repair --apply hard-refuses while pending tracking exists,
    # so next_action must surface pending_tracking first, never repair.
    target = _kickoff_target(tmp_path)
    _induce_safe_drift(target)
    (target / AEGIS_PENDING_TRACKING_REL).write_text(
        json.dumps({"events": [{"id": "p1", "tool_name": "Edit", "paths": ["src/main.ts"]}]}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    assert next_action(target, source_root=REPO_ROOT)["state"] == "pending_tracking"


def test_repair_outranks_the_plan_ladder(tmp_path: Path) -> None:
    # Drift with no scope logged yet must route to repair, not scope_required.
    target = _kickoff_target(tmp_path)
    _induce_safe_drift(target)
    assert next_action(target, source_root=REPO_ROOT)["state"] == "safe_repair_available"


def test_repairable_severity_without_substantive_action_falls_through(tmp_path: Path) -> None:
    # Adversarial-review Finding #2: a repairable-severity failure with NO substantive repair
    # action (here: git branch renamed off the task id -> branch_task_alignment fails, and the
    # only repair action present is the ever-present cosmetic normalize_plan_table) must NOT be
    # misrouted to safe_repair_available. Otherwise `repair --apply` would "fix" only the
    # cosmetic action, report success, and silently swallow the real failure. It must fall
    # through to the normal ladder (the pre-TM-225 behavior).
    target = _kickoff_target(tmp_path)
    subprocess.run(
        ["git", "branch", "-m", "feat/task-42-x", "wrong-branch-no-task-id"],
        cwd=target,
        check=True,
        capture_output=True,
    )
    state = next_action(target, source_root=REPO_ROOT)["state"]
    assert state not in {"safe_repair_available", "manual_review_repair"}, state


def test_next_action_repair_detection_is_read_only(tmp_path: Path) -> None:
    target = _kickoff_target(tmp_path)
    _induce_safe_drift(target)
    guided = next_action(target, source_root=REPO_ROOT)
    assert guided["read_only"] is True
    # Detection must not auto-restore the deleted managed file.
    assert not (target / AEGIS_LOCAL_BIN_REL).exists()


def test_detection_does_not_recurse_through_doctor(tmp_path: Path) -> None:
    # doctor() calls next_action(); next_action must use _doctor_repair_actions directly, never
    # doctor(), or this would RecursionError / hang.
    target = _kickoff_target(tmp_path)
    _induce_safe_drift(target)
    report = doctor(target, source_root=REPO_ROOT)
    assert report["status"] == "repairable"
    assert report["next_action"]["state"] == "safe_repair_available"


def test_repair_plan_split_is_single_sourced() -> None:
    safe, manual = inst._repair_plan_split(
        [{"safe": True}, {"safe": False}, {"kind": "manual_review"}, {"safe": True}]
    )
    assert len(safe) == 2 and len(manual) == 2
    # doctor() routes its split through the same helper (no divergent inline classification).
    src = (REPO_ROOT / "scripts" / "_aegis_installer.py").read_text(encoding="utf-8")
    assert "safe_actions, manual_actions = _repair_plan_split(" in src


def test_both_states_have_continuation_briefs() -> None:
    for state in ("safe_repair_available", "manual_review_repair"):
        assert state in inst.CONTINUATION_BRIEF_BY_STATE, state
        brief = inst._continuation_brief(state, "repair")
        assert brief["read_only"] is True
        assert brief["confirmation_boundary"], state
