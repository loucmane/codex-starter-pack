# Task 127 - Handoff Auto-Repair Design

## Problem
Live Aegis runs showed agents could complete source work, logging, strict verification, and closeout readiness, but still get stuck manually rewriting placeholder `HANDOFF.md` sections after `closeout_ready` reported semantic gaps.

That manual repair loop was too fragile:
- Agents had to infer what closeout wanted.
- `closeout_ready` correctly stayed read-only, so it could report gaps but not fix them.
- Final `closeout --update-handoff` could refresh handoff sections only during the final mutating closeout, which was too late for a clean preflight-and-repair cycle.

## Decision
Add a deterministic, standalone handoff repair surface:

- CLI: `aegis handoff repair --target-dir .`
- MCP: `aegis.handoff_repair`
- Core: `repair_handoff(target_dir, source_root=..., dry_run=...)`

The repair operation rebuilds only Aegis-owned semantic sections before `## Progress Log` and preserves the existing progress log unchanged.

## Behavior
- `aegis handoff repair --dry-run` previews the exact semantic handoff rewrite and writes no files.
- `aegis handoff repair` writes `HANDOFF.md` only.
- MCP `aegis.handoff_repair` is read-only by default and mutates only when `apply=true`.
- Repair writes no closeout report and does not update `.aegis/state/current-work.json`.
- Final completion still requires `aegis closeout --update-handoff`.

## Rendered Sections
The repaired semantic prefix contains:

- `## Current State`
- `## What Was Done`
- `## Implementation Evidence`
- `## Verification Evidence`
- `## Strict Verification Evidence`
- `## Current Issues/Blockers`
- `## Next Steps`
- `## Important Context`

Implementation evidence comes from `plan-step-implement`; verification evidence comes from `plan-step-verify`; strict verification evidence is `.aegis/reports/verification-report.json`.

## Why This Route
This keeps closeout strict while removing ad hoc handoff editing from the agent workflow. The agent can now do:

1. `aegis closeout --dry-run --update-handoff`
2. `aegis handoff repair` when handoff semantic gates fail
3. `aegis closeout --dry-run --update-handoff` again
4. `aegis closeout --update-handoff` only after readiness is clean

That matches the intended Aegis model: MCP/CLI manage workflow state and evidence, while normal agent tools still handle source implementation.
