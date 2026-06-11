"""Replay-cold-start A/B falsifier for the Session Zero Capsule (TM #211).

Authentic cost-measuring instrument: replay REAL historical cold-start points and run a
fresh agent against the real tree with the capsule ON vs OFF, measuring
tool-calls-to-first-meaningful-action (spec section 7) from the transcript. Unlike the
synthetic cohort (cost-blind, can only fire a KILL), this measures the dimension that
authorizes a KEEP.

Split by design:
- The TESTABLE core (transcript parsing, meaningful-action detection, worktree
  reconstruction, scoring/aggregation) runs in CI against fixtures.
- The live `claude -p` execution is OPERATOR-ONLY, gated behind
  AEGIS_RUN_COLDSTART_AB=1 so it never runs in CI (it needs the subscription, network,
  and real tokens) — same pattern as the existing wheel/MCP smoke gates.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable, Sequence

MEANINGFUL_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# Paths that are governance/scratch, not "real work" — a mutation here does not count as
# the first meaningful action (matches spec section 7's operational definition).
NON_MEANINGFUL_PREFIXES = (".aegis/", "sessions/", "plans/", "docs/ai/work-tracking/")
HOME_SCRATCH_MARKERS = ("/.claude/", "/.aegis/")
MUTATING_BASH_RE_PARTS = (
    r"\b(sed\s+-i|tee|rm|mv|cp|install|touch|chmod|chown|mkdir|rmdir)\b",
    r"(^|[;&|]\s*)git\s+(commit|add|switch\s+-c|checkout\s+-b|merge|rebase|push|reset|stash|tag)\b",
    r"(^|[;&|]\s*)task-master\s+(add-task|set-status|update|expand|remove-task|move)\b",
    r">>?\s*[^|&;]",
)


def _path_is_meaningful(rel: str) -> bool:
    text = rel.strip()
    if not text:
        return False
    if any(marker in text for marker in HOME_SCRATCH_MARKERS):
        return False
    norm = text[2:] if text.startswith("./") else text
    return not norm.startswith(NON_MEANINGFUL_PREFIXES)


def _bash_is_meaningful_mutation(command: str) -> bool:
    import re

    for part in MUTATING_BASH_RE_PARTS:
        match = re.search(part, command)
        if not match:
            continue
        # A redirect/sed/write whose only target is governance scratch is not meaningful.
        targets = re.findall(r"([\w./\-]+\.[\w]+)", command)
        if targets and all(not _path_is_meaningful(t) for t in targets):
            continue
        return True
    return False


def is_meaningful_action(tool_name: str, tool_input: dict[str, Any]) -> bool:
    """First mutation to real work, outside governance/scratch surfaces (spec section 7)."""

    if tool_name in MEANINGFUL_TOOLS:
        path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        return _path_is_meaningful(path)
    if tool_name == "Bash":
        return _bash_is_meaningful_mutation(str(tool_input.get("command") or ""))
    return False


def _iter_tool_uses(transcript_path: str | Path) -> Iterable[tuple[str, dict[str, Any]]]:
    for line in Path(transcript_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        for block in entry.get("message", {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield str(block.get("name") or ""), dict(block.get("input") or {})


def extract_first_action_cost(transcript_path: str | Path) -> dict[str, Any]:
    """Tool-calls-to-first-meaningful-action from a Claude Code transcript.

    Returns total tool calls, recon calls before the first meaningful action, the
    action itself, and whether a meaningful action was reached at all.
    """

    recon_before = 0
    total = 0
    reached = False
    first_action: dict[str, Any] | None = None
    for name, tool_input in _iter_tool_uses(transcript_path):
        total += 1
        if not reached and is_meaningful_action(name, tool_input):
            reached = True
            first_action = {"tool": name, "input_keys": sorted(tool_input.keys())}
            continue
        if not reached:
            recon_before += 1
    return {
        "reached_meaningful_action": reached,
        "recon_calls_before_first_action": recon_before if reached else total,
        "total_tool_calls": total,
        "first_action": first_action,
    }


def build_scenario_worktree(repo: Path, sha: str, dest: Path) -> Path:
    """Reconstruct a historical cold-start state as a detached worktree at `sha`."""

    repo = Path(repo).resolve()
    dest = Path(dest).resolve()
    result = subprocess.run(
        ["git", "worktree", "add", "--detach", dest.as_posix(), sha],
        cwd=repo.as_posix(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"worktree reconstruction failed for {sha}: {result.stderr.strip()}")
    return dest


def remove_worktree(repo: Path, dest: Path) -> None:
    subprocess.run(
        ["git", "worktree", "remove", "--force", Path(dest).as_posix()],
        cwd=Path(repo).resolve().as_posix(),
        capture_output=True,
        text=True,
        check=False,
    )


def score_arm(
    scenario_id: str,
    arm: str,
    cost: dict[str, Any],
    *,
    first_action_correct: bool | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "arm": arm,
        "recon_cost": cost["recon_calls_before_first_action"],
        "reached": cost["reached_meaningful_action"],
        "correct": first_action_correct,
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _paired_delta_ci(pairs: Sequence[tuple[float, float]]) -> dict[str, float]:
    """Paired delta (control - treatment) with a normal-approx 95% CI. Positive = the
    capsule reduced recon cost. Small-n, so report the CI honestly, not a p-value."""

    diffs = [control - treatment for control, treatment in pairs]
    n = len(diffs)
    mean = _mean(diffs)
    if n < 2:
        return {"delta": mean, "ci_low": mean, "ci_high": mean, "n": n}
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    se = math.sqrt(var / n)
    return {"delta": mean, "ci_low": mean - 1.96 * se, "ci_high": mean + 1.96 * se, "n": n}


def aggregate(scores: Sequence[dict[str, Any]], *, fresh_null_ids: Sequence[str] = ()) -> dict[str, Any]:
    """Aggregate paired arms into the pre-registered decision statistics."""

    by_scenario: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for score in scores:
        by_scenario.setdefault(score["scenario_id"], {}).setdefault(score["arm"], []).append(score)

    decision_pairs: list[tuple[float, float]] = []
    fresh_null_pairs: list[tuple[float, float]] = []
    per_scenario: list[dict[str, Any]] = []
    capsule_correct = 0
    baseline_correct = 0
    correctness_scored = 0
    for scenario_id, arms in by_scenario.items():
        if "capsule" not in arms or "baseline" not in arms:
            continue
        cap_cost = _mean([s["recon_cost"] for s in arms["capsule"] if s["reached"]] or [s["recon_cost"] for s in arms["capsule"]])
        base_cost = _mean([s["recon_cost"] for s in arms["baseline"] if s["reached"]] or [s["recon_cost"] for s in arms["baseline"]])
        pair = (base_cost, cap_cost)
        (fresh_null_pairs if scenario_id in fresh_null_ids else decision_pairs).append(pair)
        for arm_name, arm_scores in arms.items():
            for s in arm_scores:
                if s.get("correct") is None:
                    continue
                correctness_scored += 1
                if s["correct"] and arm_name == "capsule":
                    capsule_correct += 1
                elif s["correct"] and arm_name == "baseline":
                    baseline_correct += 1
        per_scenario.append(
            {
                "scenario_id": scenario_id,
                "capsule_recon": round(cap_cost, 2),
                "baseline_recon": round(base_cost, 2),
                "delta": round(base_cost - cap_cost, 2),
                "fresh_null": scenario_id in fresh_null_ids,
            }
        )
    decision = _paired_delta_ci(decision_pairs)
    fresh_null = _paired_delta_ci(fresh_null_pairs)
    return {
        "decision_delta_recon": decision,
        "fresh_null_delta_recon": fresh_null,
        "per_scenario": per_scenario,
        "correctness": {
            "capsule_correct": capsule_correct,
            "baseline_correct": baseline_correct,
            "scored": correctness_scored,
        },
    }


def decide(aggregated: dict[str, Any], *, min_delta: float = 1.0, fresh_null_tol: float = 0.5) -> dict[str, Any]:
    """Pre-registered verdict. KEEP requires a real recon reduction whose CI clears 0 AND
    a passing fresh-null (clean state shows ~no edge). Anything else KILL/INCONCLUSIVE —
    the instrument is built to fire a true negative, never to manufacture a KEEP."""

    decision = aggregated["decision_delta_recon"]
    fresh = aggregated["fresh_null_delta_recon"]
    fresh_violated = fresh["n"] > 0 and abs(fresh["delta"]) > fresh_null_tol
    if fresh_violated:
        return {
            "recommendation": "INCONCLUSIVE",
            "reason": f"fresh-null violated (clean-state delta {fresh['delta']:.2f} > tol {fresh_null_tol}); battery is capsule-shaped",
        }
    if decision["n"] < 2:
        return {"recommendation": "INCONCLUSIVE", "reason": "too few decision scenarios for a CI"}
    if decision["delta"] >= min_delta and decision["ci_low"] > 0:
        return {
            "recommendation": "KEEP-ELIGIBLE",
            "reason": f"capsule cut recon cost by {decision['delta']:.2f} (CI {decision['ci_low']:.2f}..{decision['ci_high']:.2f}); confirm with spec section 7 live A/B before retiring scaffolding",
        }
    if decision["ci_high"] <= 0:
        return {"recommendation": "KILL", "reason": "capsule did not reduce recon cost (CI entirely <= 0)"}
    return {"recommendation": "INCONCLUSIVE", "reason": f"recon delta {decision['delta']:.2f} CI straddles 0 / below {min_delta}"}


def render_report(aggregated: dict[str, Any], verdict: dict[str, Any]) -> str:
    lines = ["# Replay-cold-start A/B — capsule falsifier"]
    d = aggregated["decision_delta_recon"]
    f = aggregated["fresh_null_delta_recon"]
    lines.append(f"decision recon delta (baseline-capsule): {d['delta']:.2f}  CI[{d['ci_low']:.2f},{d['ci_high']:.2f}]  n={d['n']}")
    lines.append(f"fresh-null recon delta: {f['delta']:.2f}  n={f['n']} (must be ~0)")
    c = aggregated["correctness"]
    lines.append(f"first-action correctness: capsule {c['capsule_correct']} vs baseline {c['baseline_correct']} (of {c['scored']} scored)")
    for row in aggregated["per_scenario"]:
        tag = " [fresh-null]" if row["fresh_null"] else ""
        lines.append(f"- {row['scenario_id']}: capsule {row['capsule_recon']} vs baseline {row['baseline_recon']} recon (Δ{row['delta']}){tag}")
    lines.append(f"VERDICT: {verdict['recommendation']} — {verdict['reason']}")
    return "\n".join(lines) + "\n"


# ───────────────────────── OPERATOR-ONLY LIVE EXECUTION ─────────────────────────
# Everything below runs real `claude -p` sessions: subscription tokens, network,
# nondeterminism. It is gated behind AEGIS_RUN_COLDSTART_AB=1 so CI never touches it
# (same pattern as the wheel/MCP smoke gates). The testable core above is what runs in CI.
RUN_GATE_ENV = "AEGIS_RUN_COLDSTART_AB"
RESUME_PROMPT = "Continue. Get oriented in this repo and take the next concrete step on the active work."


def _newest_transcript(project_dir: Path, since_mtime: float) -> Path | None:
    candidates = [p for p in project_dir.glob("*.jsonl") if p.stat().st_mtime > since_mtime]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def run_live_ab(
    repo: str | Path,
    scenarios: Sequence[dict[str, Any]],
    *,
    k: int = 3,
    allowed_tools: Sequence[str] = ("Bash", "Read", "Edit", "Write", "Grep", "Glob"),
) -> dict[str, Any]:
    """Operator-only: replay each scenario's real cold-start, capsule ON vs OFF, k times.

    Requires AEGIS_RUN_COLDSTART_AB=1. Each scenario is {scenario_id, sha, fresh_null?}.
    Returns the aggregated decision + verdict. Worktrees are created and removed per run.
    """

    if os.environ.get(RUN_GATE_ENV) != "1":
        raise RuntimeError(
            f"live cold-start A/B is operator-only; set {RUN_GATE_ENV}=1 to run real claude -p sessions"
        )
    repo = Path(repo).resolve()
    import tempfile

    scores: list[dict[str, Any]] = []
    fresh_ids = [s["scenario_id"] for s in scenarios if s.get("fresh_null")]
    home_projects = Path.home() / ".claude" / "projects"
    for scenario in scenarios:
        for arm in ("capsule", "baseline"):
            for _ in range(k):
                with tempfile.TemporaryDirectory(prefix="aegis-coldstart-") as tmp:
                    wt = build_scenario_worktree(repo, scenario["sha"], Path(tmp) / "wt")
                    try:
                        env = dict(os.environ)
                        env.pop(RUN_GATE_ENV, None)  # the replay agent must not recurse
                        # Household rule: replay agents run on the Max subscription, never
                        # API credits. A present ANTHROPIC_API_KEY routes claude -p down the
                        # API-credit path; drop it so the subscription auth is used.
                        env.pop("ANTHROPIC_API_KEY", None)
                        # Explicit per-arm override: with session-hash A/B assignment in
                        # brief.json, an unset env would randomize the capsule arm.
                        env["AEGIS_CAPSULE"] = "off" if arm == "baseline" else "on"
                        project_dir = home_projects / wt.as_posix().replace("/", "-")
                        before = project_dir.stat().st_mtime if project_dir.exists() else 0.0
                        subprocess.run(
                            ["claude", "-p", RESUME_PROMPT, "--allowedTools", *allowed_tools],
                            cwd=wt.as_posix(),
                            capture_output=True,
                            text=True,
                            env=env,
                            timeout=600,
                            check=False,
                        )
                        transcript = _newest_transcript(project_dir, before) if project_dir.exists() else None
                        cost = (
                            extract_first_action_cost(transcript)
                            if transcript
                            else {"recon_calls_before_first_action": 0, "reached_meaningful_action": False, "total_tool_calls": 0, "first_action": None}
                        )
                        scores.append(score_arm(scenario["scenario_id"], arm, cost))
                    finally:
                        remove_worktree(repo, wt)
    aggregated = aggregate(scores, fresh_null_ids=fresh_ids)
    verdict = decide(aggregated)
    return {"aggregated": aggregated, "verdict": verdict, "raw_scores": scores}


__all__ = [
    "RESUME_PROMPT",
    "RUN_GATE_ENV",
    "aggregate",
    "build_scenario_worktree",
    "decide",
    "extract_first_action_cost",
    "is_meaningful_action",
    "remove_worktree",
    "render_report",
    "run_live_ab",
    "score_arm",
]
