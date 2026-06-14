"""TM 221: the drain must not accrete read-only events into required closeout evidence.

Draining a pre-#224 pending-tracking backlog via `aegis log --pending-id` used to copy each
drained event's evidence into the plan-step Evidence cell, so closeout.evidence.* then
required all that inspection noise. The fix classifies the stored event at drain time (strict,
fail-KEEP) and, when it is read-only, discards it from the queue WITHOUT accreting. A batch
purge cleans an existing backlog. The invariant: a genuine mutation's evidence is still
required; only read-only-event-derived evidence is excluded — apply-gated MCP tools are KEPT.
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
    AEGIS_PENDING_TRACKING_REL,
    install,
    kickoff,
    log_work,
    purge_read_only_pending,
)


# --- classifier (strict, fail-KEEP) ------------------------------------------------

CLASSIFIER_CASES = [
    ("Bash", "cmd`cat app/src/lib/nogPrompt.ts`", True),
    ("Bash", "cmd`git status --short`", True),
    ("Bash", "cmd`sed -i 's/a/b/' src/x.ts`", False),       # in-place mutation
    ("Bash", "/tmp/task81-vite.log", False),                # redirect-target => mutation
    ("Edit", "app/src/lib/nogPrompt.ts", False),            # real edit => keep
    ("Write", "src/new.ts", False),
    ("mcp__playwright__browser_click", "x", True),
    ("mcp__chrome-devtools__take_snapshot", "x", True),
    ("mcp__taskmaster_ai__get_tasks", "x", True),
    ("mcp__taskmaster_ai__next_task", "x", True),
    ("mcp__aegis__aegis_inspect", "x", False),              # conservatively kept (target-dir hole)
    ("mcp__aegis__aegis_repair", "x", False),               # APPLY-GATED => kept (the escape)
    ("mcp__aegis__aegis_runtime_update", "x", False),
    ("mcp__taskmaster_ai__set_task_status", "x", False),
    ("mcp__aegis__aegis_closeout", "x", False),
]


@pytest.mark.parametrize(("tool", "evidence", "expect"), CLASSIFIER_CASES)
def test_stored_event_classifier(tool: str, evidence: str, expect: bool) -> None:
    got = inst._stored_event_is_read_only(REPO_ROOT, {"tool": tool, "evidence": evidence, "id": "i"})
    assert got is expect, f"{tool} | {evidence}"


def test_classifier_fail_keeps_when_gate_lib_missing(tmp_path: Path) -> None:
    # No .claude/scripts/gate_lib.py under target -> cannot classify -> KEEP (mutation).
    bare = tmp_path / "bare"
    bare.mkdir()
    assert inst._stored_event_is_read_only(bare, {"tool": "Bash", "evidence": "cmd`cat x`"}) is False


def test_classifier_fail_keeps_when_gate_lib_broken(tmp_path: Path) -> None:
    bare = tmp_path / "broken"
    (bare / ".claude" / "scripts").mkdir(parents=True)
    (bare / ".claude" / "scripts" / "gate_lib.py").write_text("this is not valid python !!!", encoding="utf-8")
    inst._TARGET_GATE_LIB_CACHE.clear()
    assert inst._stored_event_is_read_only(bare, {"tool": "Bash", "evidence": "cmd`cat x`"}) is False
    inst._TARGET_GATE_LIB_CACHE.clear()


# --- batch purge -------------------------------------------------------------------


def seed_pending(target: Path, events: list[dict]) -> None:
    (target / ".aegis" / "state").mkdir(parents=True, exist_ok=True)
    (target / ".aegis" / "state" / "pending-tracking.json").write_text(
        json.dumps({"schema_version": "1.0.0", "events": events}), encoding="utf-8"
    )


def make_target_with_gate_lib(tmp_path: Path) -> Path:
    """Minimal target carrying the live gate_lib so the classifier resolves."""
    target = tmp_path / "t"
    (target / ".claude" / "scripts").mkdir(parents=True)
    (target / ".claude" / "scripts" / "gate_lib.py").write_text(
        (REPO_ROOT / ".claude" / "scripts" / "gate_lib.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return target


def test_batch_purge_preview_then_apply(tmp_path: Path) -> None:
    target = make_target_with_gate_lib(tmp_path)
    events = [
        {"id": "ro1", "tool": "Bash", "evidence": "cmd`cat app/x.ts`"},
        {"id": "ro2", "tool": "mcp__playwright__browser_click", "evidence": "x"},
        {"id": "mut1", "tool": "Edit", "evidence": "app/x.ts"},
        {"id": "mut2", "tool": "mcp__aegis__aegis_repair", "evidence": "x"},  # apply-gated kept
    ]
    seed_pending(target, events)
    inst._TARGET_GATE_LIB_CACHE.clear()

    preview = purge_read_only_pending(target, apply=False)
    assert preview["status"] == "preview"
    assert preview["read_only_count"] == 2
    assert set(preview["purged_ids"]) == {"ro1", "ro2"}
    # preview must NOT mutate the queue
    assert len(json.loads((target / ".aegis/state/pending-tracking.json").read_text())["events"]) == 4

    applied = purge_read_only_pending(target, apply=True)
    assert applied["applied"] is True
    remaining = json.loads((target / ".aegis/state/pending-tracking.json").read_text())["events"]
    assert {e["id"] for e in remaining} == {"mut1", "mut2"}, "mutations (incl. apply-gated) retained"


# --- drain-gate in log_work (integration) ------------------------------------------


def make_kicked_off_repo(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    target.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=target, capture_output=True, check=False)
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    marker = target / ".aegis" / "state" / "client-reload-required.json"
    if marker.exists():
        marker.unlink()
    kickoff(target, task_id="80", slug="drain", title="Drain")
    return target


def current_plan_path(target: Path) -> Path:
    work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
    return target / work["paths"]["plan"]


def test_drain_readonly_event_discards_without_accreting(tmp_path: Path) -> None:
    target = make_kicked_off_repo(tmp_path)
    seed_pending(target, [{"id": "roX", "tool": "Bash", "evidence": "cmd`cat app/src/lib/nogPrompt.ts`",
                           "handler": "bash:cat", "task": {"id": "80", "slug": "drain"}}])
    inst._TARGET_GATE_LIB_CACHE.clear()
    plan_before = current_plan_path(target).read_text(encoding="utf-8")

    result = log_work(target, pending_event_id="roX", note="drain read-only", plan_step="plan-step-verify", plan_status="completed")

    assert result["status"] == "purged_read_only"
    # queue drained, and the noise token NEVER reached the plan cell
    assert not (target / ".aegis/state/pending-tracking.json").exists()
    assert "nogPrompt.ts" not in current_plan_path(target).read_text(encoding="utf-8")
    assert current_plan_path(target).read_text(encoding="utf-8") == plan_before


def test_drain_mutation_event_still_accretes(tmp_path: Path) -> None:
    target = make_kicked_off_repo(tmp_path)
    (target / "src").mkdir(exist_ok=True)
    (target / "src" / "real.ts").write_text("x\n", encoding="utf-8")
    seed_pending(target, [{"id": "mutX", "tool": "Edit", "evidence": "src/real.ts",
                           "handler": "claude:Edit", "task": {"id": "80", "slug": "drain"}}])
    inst._TARGET_GATE_LIB_CACHE.clear()

    result = log_work(target, pending_event_id="mutX", note="logged real edit", plan_step="plan-step-implement", plan_status="completed")

    assert result["status"] == "logged"
    assert "src/real.ts" in current_plan_path(target).read_text(encoding="utf-8"), "real mutation evidence still required"
