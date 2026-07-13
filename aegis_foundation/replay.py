"""Aegis replay harness (TM #195, Phase 0).

Runs recorded or synthetic tool-call corpora through the REAL gate code (never a
reimplementation) under synthesized workflow states, and reports verdict deltas. This
is the measurement substrate the program's standing rule depends on: no gate-behavior
change ships unreplayed.

Corpus entry schema (JSONL, one object per line):
    {
      "id": "E04",
      "label": "fp_workflow_state" | "ceremony_interior" | "must_allow"
               | "must_fire" | "adversarial_must_block" | "recorded",
      "state": "blocked_strict" | "ready_strict" | "ready_strict_pending"
               | "observation_strict" | "blocked_advisory" | "ready_advisory",
      "hook": "pretooluse" | "stop",
      "payload": {"tool_name": ..., "tool_input": {...}},   # omitted for stop
      "expected_gap": false,            # adversarial entries the CURRENT policy misses
      "notes": "..."
    }

Label semantics:
- must_allow            blocked => REGRESSION (legitimate work newly taxed)
- must_fire             allowed => REGRESSION (a completeness boundary stopped firing)
- adversarial_must_block allowed and not expected_gap => REGRESSION;
                         allowed and expected_gap => STANDING GAP (reported, not fatal)
- fp_workflow_state / ceremony_interior
                        historical false positives: blocking is the BASELINE, not a
                        failure; the count must only ever go down. A block-to-allow
                        flip is an improvement and is reported as one.
- recorded              informational replay of ingested live events.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPLAY_SCHEMA_VERSION = "1"
LABELS = (
    "fp_workflow_state",
    "ceremony_interior",
    "must_allow",
    "must_fire",
    "adversarial_must_block",
    "recorded",
)
STATES = (
    "blocked_strict",
    "ready_strict",
    "ready_strict_pending",
    "observation_strict",
    "blocked_advisory",
    "ready_advisory",
)


def _run(
    cmd: list[str], cwd: Path, *, input_text: str = "", env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=str(cwd), input=input_text, text=True, capture_output=True, env=env, check=False
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_state_fixture(base_dir: Path, state: str) -> Path:
    """Synthesize a repo in the named workflow state for the real gate to evaluate."""

    if state not in STATES:
        raise ValueError(f"unknown replay state: {state}")
    repo = base_dir / state
    repo.mkdir(parents=True, exist_ok=True)
    assert _run(["git", "init", "-q"], repo).returncode == 0
    advisory = state.endswith("_advisory")
    if advisory:
        _write(
            repo / ".aegis" / "state" / "enforcement.json",
            json.dumps(
                {
                    "mode": "advisory",
                    "set_at": "2026-06-10T00:00:00Z",
                    "set_by": "replay",
                    "reason": "replay",
                }
            ),
        )
    if state.startswith("blocked"):
        _run(["git", "checkout", "-q", "-b", "main"], repo)
        return repo

    branch = "feat/task-103-claude-runtime-adapter"
    _run(["git", "checkout", "-q", "-b", branch], repo)
    _write(
        repo / ".taskmaster" / "tasks" / "tasks.json",
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {"id": 103, "title": "Claude Runtime Adapter", "status": "in-progress"}
                    ]
                }
            }
        ),
    )
    session_rel = Path("2026/06/2026-06-10-001-task103-claude-runtime-adapter.md")
    _write(repo / "sessions" / session_rel, "# Task 103 Session\n")
    (repo / "sessions" / "current").symlink_to(session_rel)
    _write(
        repo / "sessions" / "state.json",
        json.dumps(
            {"current": session_rel.name, "paused": [], "updated_at": "2026-06-10T00:00:00+00:00"}
        ),
    )
    plan_rel = Path("2026-06-10-task103-claude-runtime-adapter.md")
    _write(
        repo / "plans" / plan_rel,
        "---\ntask_ids: [103]\n---\n\n# Plan - Task 103\n\n"
        "| Step ID | Description | Evidence | Status |\n| --- | --- | --- | --- |\n"
        "| plan-step-scope | Scope | evidence | completed |\n"
        "| plan-step-implement | Implement | evidence | pending |\n"
        "| plan-step-verify | Verify | evidence | pending |\n",
    )
    (repo / "plans" / "current").symlink_to(plan_rel)
    _write(
        repo
        / "docs"
        / "ai"
        / "work-tracking"
        / "active"
        / "20260610-task103-claude-runtime-adapter-ACTIVE"
        / "TRACKER.md",
        "# Task 103 Tracker\n\n## Plan Compliance Checklist\n"
        "- [x] plan-step-scope - Scope\n- [ ] plan-step-implement - Implement\n- [ ] plan-step-verify - Verify\n",
    )
    if state == "observation_strict":
        _write(
            repo / ".aegis" / "state" / "current-work.json",
            json.dumps(
                {
                    "schema_version": "1",
                    "status": "in-progress",
                    "mode": "observation",
                    "task": {
                        "id": "103",
                        "slug": "claude-runtime-adapter",
                        "status": "in-progress",
                    },
                }
            ),
        )
    if state == "ready_strict_pending":
        _write(
            repo / ".aegis" / "state" / "current-work.json",
            json.dumps(
                {
                    "schema_version": "1",
                    "status": "in-progress",
                    "task": {
                        "id": "103",
                        "slug": "claude-runtime-adapter",
                        "status": "in-progress",
                    },
                }
            ),
        )
        _write(
            repo / ".aegis" / "state" / "pending-tracking.json",
            json.dumps(
                {
                    "events": [
                        {
                            "id": "replayp",
                            "created_at": "2026-06-10T00:00:00Z",
                            "updated_at": "2026-06-10T00:00:00Z",
                            "tool": "Bash",
                            "handler": "bash:rg",
                            "evidence": "cmd`rg -n pattern file`",
                            "task": {"id": "103", "slug": "claude-runtime-adapter"},
                            "mode": "strict",
                            "reason": "replay pending fixture",
                        }
                    ]
                }
            ),
        )
    return repo


def run_entry(
    entry: dict[str, Any], source_root: Path, fixtures_dir: Path, fixture_cache: dict[str, Path]
) -> dict[str, Any]:
    state = str(entry.get("state") or "ready_strict")
    if state not in fixture_cache:
        fixture_cache[state] = build_state_fixture(fixtures_dir, state)
    repo = fixture_cache[state]
    hook = str(entry.get("hook") or "pretooluse")
    gate = source_root / ".claude" / "scripts" / "gate_lib.py"
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    env["XDG_STATE_HOME"] = str(fixtures_dir / "state-home")
    payload = entry.get("payload") or {}
    result = _run(
        [sys.executable, gate.as_posix(), hook],
        repo,
        input_text=json.dumps(payload) if hook == "pretooluse" else "",
        env=env,
    )
    verdict = "allow" if result.returncode == 0 else "block"
    return {
        "id": entry.get("id"),
        "label": entry.get("label"),
        "state": state,
        "hook": hook,
        "verdict": verdict,
        "returncode": result.returncode,
        "expected_gap": bool(entry.get("expected_gap")),
        "notes": entry.get("notes"),
        "stderr_head": (result.stderr or "").splitlines()[:2],
    }


def evaluate(results: list[dict[str, Any]]) -> dict[str, Any]:
    regressions: list[dict[str, Any]] = []
    standing_gaps: list[dict[str, Any]] = []
    improvements: list[dict[str, Any]] = []
    fp_baseline = 0
    by_label: dict[str, dict[str, int]] = {}
    for result in results:
        label = str(result.get("label"))
        verdict = result.get("verdict")
        counts = by_label.setdefault(label, {"allow": 0, "block": 0})
        counts[verdict] = counts.get(verdict, 0) + 1
        if label == "must_allow" and verdict == "block":
            regressions.append(result)
        elif label == "must_fire" and verdict == "allow":
            regressions.append(result)
        elif label == "adversarial_must_block" and verdict == "allow":
            (standing_gaps if result.get("expected_gap") else regressions).append(result)
        elif label in {"fp_workflow_state", "ceremony_interior"}:
            if verdict == "block":
                fp_baseline += 1
            else:
                improvements.append(result)
    return {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "total": len(results),
        "by_label": by_label,
        "fp_baseline": fp_baseline,
        "regressions": regressions,
        "standing_gaps": standing_gaps,
        "improvements": improvements,
        "passed": not regressions,
    }


def load_corpus(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.strip().startswith("#"):
                entries.append(json.loads(line))
    return entries


def run_corpus(
    corpus_paths: Iterable[str | Path], *, source_root: str | Path, work_dir: str | Path
) -> dict[str, Any]:
    source = Path(source_root).resolve()
    fixtures_dir = Path(work_dir).resolve()
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    fixture_cache: dict[str, Path] = {}
    results = [
        run_entry(entry, source, fixtures_dir, fixture_cache) for entry in load_corpus(corpus_paths)
    ]
    report = evaluate(results)
    report["results"] = results
    report_path = fixtures_dir / "aegis-replay-report.json"
    report["report_path"] = report_path.as_posix()
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def ingest_ledger(
    root: str | Path,
    *,
    branch: str | None = None,
    all_branches: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    """Convert this repo's live ledger into replay-corpus candidates.

    Bash commands and file-tool paths survive in the recorded events, so those are
    reconstructable; everything else is counted as non-replayable (the recorder-gap
    finding: digests alone cannot be re-evaluated).
    """

    script = Path(__file__).resolve().parents[1] / ".claude" / "scripts" / "ledger_lib.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("_replay_ledger_lib", script)
    if spec is None or spec.loader is None:
        return [], 0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = Path(root).resolve()
    context = module.repository_context(target)
    selected_branch = branch or context.get("branch")
    ledger = module.open_ledger(cwd=target)
    try:
        events = ledger.read() if all_branches else ledger.read(branch=selected_branch)
    finally:
        ledger.close()
    repository = context.get("repository_identity")
    events = [
        event
        for event in events
        if not event.get("repository_identity") or event.get("repository_identity") == repository
    ]
    candidates: list[dict[str, Any]] = []
    skipped = 0
    for event in events:
        if event.get("event_type") not in {"mutation", "verification", "delivery", "task_truth"}:
            continue
        extra = event.get("extra") or {}
        tool = event.get("tool_name")
        if tool == "Bash" and extra.get("command"):
            payload = {"tool_name": "Bash", "tool_input": {"command": extra["command"]}}
        elif tool in {"Edit", "Write"} and event.get("paths"):
            payload = {"tool_name": tool, "tool_input": {"file_path": event["paths"][0]}}
        else:
            skipped += 1
            continue
        candidates.append(
            {
                "id": f"ledger-{event.get('event_id')}",
                "label": "recorded",
                "state": "ready_advisory",
                "hook": "pretooluse",
                "payload": payload,
                "notes": (
                    f"ingested from ledger ts={event.get('ts')} "
                    f"type={event.get('event_type')} branch={event.get('branch')}"
                ),
            }
        )
    return candidates, skipped


def render_report(report: dict[str, Any]) -> str:
    lines = [f"# Aegis replay — {report.get('total')} entries"]
    for label, counts in sorted(report.get("by_label", {}).items()):
        lines.append(f"- {label}: allow={counts.get('allow', 0)} block={counts.get('block', 0)}")
    lines.append(f"- FP baseline (historical blocks still blocking): {report.get('fp_baseline')}")
    for improvement in report.get("improvements", []):
        lines.append(
            f"- IMPROVEMENT: {improvement.get('id')} now allows ({improvement.get('notes')})"
        )
    for gap in report.get("standing_gaps", []):
        lines.append(
            f"- STANDING GAP (expected): {gap.get('id')} still allowed — {gap.get('notes')}"
        )
    for regression in report.get("regressions", []):
        lines.append(
            f"- REGRESSION: {regression.get('id')} [{regression.get('label')}] verdict={regression.get('verdict')} — {regression.get('notes')}"
        )
    lines.append(f"Result: {'PASS' if report.get('passed') else 'FAIL'}")
    return "\n".join(lines) + "\n"


__all__ = [
    "LABELS",
    "STATES",
    "build_state_fixture",
    "evaluate",
    "ingest_ledger",
    "load_corpus",
    "render_report",
    "run_corpus",
]
