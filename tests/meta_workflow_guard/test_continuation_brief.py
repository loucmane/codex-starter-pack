"""TM 189: the per-state continuation brief that `aegis next` attaches to its guidance.

TM 188 installed the cross-agent continuation *contract* (a document). TM 189 makes the
running tool speak it: every `aegis next` payload now carries a `continuation_brief` that
says, for the current workflow state, exactly what a bare "continue" authorises — one safe
step, with explicit confirmation boundaries and stop conditions, and never an automatic
merge/push. These tests lock that the brief reaches every state, stays read-only, names the
active task authority so "continue" can't be misread as "switch tasks", and never authorises
an irreversible action.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import _aegis_installer as inst  # noqa: E402
from scripts._aegis_installer import install, kickoff, next_action  # noqa: E402

REQUIRED_KEYS = {
    "workflow_phase",
    "current_task_authority",
    "continue_means",
    "next_safe_action",
    "confirmation_boundary",
    "artifact_policy",
    "stop_conditions",
    "read_only",
}

# next_safe_action must always be a single safe verb, never a raw irreversible git op.
FORBIDDEN_ACTIONS = {"merge", "push", "force_push", "force-push", "reset", "reset_hard", "pr_merge"}


def all_table_briefs() -> dict[str, dict]:
    return {
        state: inst._continuation_brief(state, "phase")
        for state in inst.CONTINUATION_BRIEF_BY_STATE
    }


def test_payload_always_carries_a_read_only_brief() -> None:
    payload = inst._workflow_guidance_payload(
        phase="implement",
        state="implementation_required",
        next_required_action="x",
        suggested_cli="y",
        current_task_authority="taskmaster:189",
    )
    brief = payload["continuation_brief"]
    assert REQUIRED_KEYS <= set(brief)
    assert brief["read_only"] is True
    assert payload["read_only"] is True
    assert brief["current_task_authority"] == "taskmaster:189"


def test_every_table_state_yields_a_coherent_brief() -> None:
    for state, brief in all_table_briefs().items():
        assert REQUIRED_KEYS <= set(brief), state
        assert brief["continue_means"].strip(), f"{state}: empty continue_means"
        assert brief["next_safe_action"].strip(), f"{state}: empty next_safe_action"
        assert brief["read_only"] is True, state


def test_unknown_state_falls_back_without_crashing() -> None:
    brief = inst._continuation_brief("totally_unknown_state", "phase")
    assert REQUIRED_KEYS <= set(brief)
    assert brief["next_safe_action"] == "totally_unknown_state"
    assert brief["current_task_authority"] == "none"
    assert brief["read_only"] is True


def test_universal_stops_present_in_every_brief() -> None:
    # readiness-BLOCKED and unlogged pending tracking always halt a continuation, no matter
    # the state — these mirror the TM 188 contract's hard stops.
    for state, brief in all_table_briefs().items():
        stops = " ".join(brief["stop_conditions"]).lower()
        assert "readiness blocked" in stops, state
        assert "pending tracking unlogged" in stops, state


def test_brief_never_authorises_an_irreversible_action() -> None:
    # The autonomy-safety invariant (matches test_continuation_contract): no continuation
    # intent auto-merges/pushes. merge/push may only be NAMED as a confirmation boundary, and
    # such a boundary must require explicit approval/confirmation.
    briefs = all_table_briefs()
    briefs["__fallback__"] = inst._continuation_brief("unknown", "phase")
    for state, brief in briefs.items():
        action_text = f"{brief['continue_means']} {brief['next_safe_action']}".lower()
        for forbidden in ("merge", "force-push", "force push", "auto-merge", "automatically"):
            assert (
                forbidden not in action_text
            ), f"{state}: '{forbidden}' must not be an auto action"
        assert brief["next_safe_action"] not in FORBIDDEN_ACTIONS, state
        boundary = [b.lower() for b in brief["confirmation_boundary"]]
        if any("merge" in b for b in boundary):
            joined = " ".join(boundary)
            assert "approval" in joined or "confirmation" in joined or "explicit" in joined, state


def test_delivery_and_completion_states_follow_repository_authority_policy() -> None:
    # After closeout, attended/default policy still requires confirmation. A valid active
    # evidence-gated policy may delegate only an eligible exact-head merge to trusted CI.
    for state in ("closeout_passed", "delivery_pending"):
        brief = inst._continuation_brief(state, "deliver")
        boundary = " ".join(brief["confirmation_boundary"]).lower()
        assert "attended" in boundary and "confirmation" in boundary, state
        assert "policy" in boundary, state
        assert brief["next_safe_action"] not in FORBIDDEN_ACTIONS, state
    pending = inst._continuation_brief("delivery_pending", "deliver")
    boundary = " ".join(pending["confirmation_boundary"]).lower()
    assert "evidence-gated" in boundary
    assert "eligible exact-head merge" in boundary
    unknown = inst._continuation_brief("delivery_unknown", "deliver")
    assert unknown["next_safe_action"] == "inspect_git_state"


def test_closeout_brief_tracks_the_contract_vocabulary() -> None:
    # Single-source discipline: dry-run remains the next safe step; only an active policy can
    # authorize verified non-dry-run closeout without a new chat approval.
    brief = inst._continuation_brief("closeout_required", "closeout")
    assert "dry-run" in brief["continue_means"]
    assert "evidence-gated policy may authorize" in brief["continue_means"]
    assert "attended/default" in " ".join(brief["confirmation_boundary"])
    # The contract constant is the upstream source the doc renders from.
    assert "exactly ONE safe step" in inst.AEGIS_CONTINUATION_SUMMARY


def test_current_task_authority_threads_through_next_action(tmp_path: Path) -> None:
    # End-to-end: an active task must surface as the brief's authority so a bare "continue"
    # cannot be read as "pick a different task".
    target = tmp_path / "brief-authority"
    target.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)
    (target / "src").mkdir()
    (target / "src" / "main.ts").write_text("export const ready = true;\n", encoding="utf-8")
    install(target, source_root=REPO_ROOT, primary_agent="codex", agents=["codex"], apply=True)
    kickoff(
        target,
        task_id="42",
        slug="task-42-add-button",
        title="Add visible button",
        source_root=REPO_ROOT,
    )
    guided = next_action(target, source_root=REPO_ROOT)
    assert guided["state"] == "scope_required"
    brief = guided["continuation_brief"]
    assert brief["current_task_authority"] == "taskmaster:42"
    assert "switch the active task" in " ".join(
        inst._continuation_brief("implementation_required", "implement")["confirmation_boundary"]
    )


def test_format_next_summary_is_actionable_and_read_only() -> None:
    payload = inst._workflow_guidance_payload(
        phase="implement",
        state="implementation_required",
        next_required_action="make the change",
        suggested_cli="aegis log ...",
        current_task_authority="taskmaster:189",
    )
    text = inst.format_next_summary(payload)
    assert "Aegis next: implementation_required" in text
    assert "taskmaster:189" in text
    assert payload["continuation_brief"]["continue_means"] in text
    assert "read-only guidance" in text
    assert (
        "merge" not in text.lower().split("stop if")[0]
    )  # no merge instruction before the stop line


def test_next_cli_defaults_to_summary_json_flag_emits_payload(tmp_path: Path) -> None:
    base = [sys.executable, "-m", "aegis_foundation.cli", "next", "--target-dir", str(tmp_path)]
    summary = subprocess.run(base, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert summary.returncode == 0, summary.stderr
    assert summary.stdout.startswith("Aegis next:"), summary.stdout[:80]
    assert not summary.stdout.lstrip().startswith("{")

    raw = subprocess.run(
        base + ["--json"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert raw.returncode == 0, raw.stderr
    payload = json.loads(raw.stdout)
    assert "continuation_brief" in payload
    assert payload["continuation_brief"]["read_only"] is True
