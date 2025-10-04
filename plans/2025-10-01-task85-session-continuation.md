---
session_id: 2025-10-01-001
work_context: task85-session-continuation
handler_target: templates/workflows/session/continuation
task_ids: [85]
branch_policy: feature-required
evidence_summary:
  - reports/session-continuation/*
  - reports/meta-workflow-guard/guard-*.txt
  - pytest logs for session continuation regression suite
plan_version: v1
emergency_bypass: false
---

# Plan – Task 85 Session Continuation & State Workflows

## Header
- **Session ID (S)**: 2025-10-01-001
- **Work Context (W)**: task85-session-continuation
- **Handler Target (H)**: templates/workflows/session/continuation
- **Task IDs**: 85
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: reports/session-continuation/*, guard + pytest logs
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                        | Evidence                                              | Status  |
|---------------------|--------------------------------------------------------------------|-------------------------------------------------------|---------|
| plan-step-scope     | Inventory continuation/state references + define migration targets | Session log + tracker entries + docs/ai/work-tracking/active/20251001-task85-session-continuation-ACTIVE/designs/session-continuation-inventory.md | completed |
| plan-step-implement | Build workflows/handlers, update registry + guard, add regression  | docs/ai/work-tracking/active/20251001-task85-session-continuation-ACTIVE/designs/continuation-workflow-updates.md, templates/workflows/session/continuation.md, templates/workflows/session/state-management.md, templates/REGISTRY.md, tests/session_continuation/test_metadata.py, tests/session_continuation/README.md | in_progress |
| plan-step-verify    | Final guard/test runs, docs updated, handoff captured               | Guard + pytest logs, updated docs + Serena memory     | pending |
| plan-step-emergency | _Optional_ – only if bypass required                                | Waiver + post-mortem plan                             | n/a     |

## Scope
- `templates/workflows/session/continuation.md`
- `templates/workflows/session/state-recovery.md`
- `templates/registry/session/*.md`
- `templates/handlers/orchestrators/session/continuation.md`
- `templates/handlers/orchestrators/session/state-recovery.md`
- `templates/behaviors/session/continuation/*.md`
- `templates/behaviors/session/continuation-validation.md`
- `scripts/codex-guard` (continuation enforcement rules)
- `tests/session_continuation/*` (new regression suite)
- `docs/ai/work-tracking/active/20251001-task85-session-continuation-ACTIVE/*`

## Branch Policy
- Current branch: `feat/task85-session-continuation-workflows` (must remain aligned)
- No direct commits to `main` for this plan.

## Amendments & Versioning
- _None yet_

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Activate Serena project `codex` and read `session_2025-09-30_timestamp_guard` + future Task 85 memories.
  2. Review work-tracking folder `20251001-task85-session-continuation-ACTIVE/` (Tracker, Implementation, Findings).
  3. Run `python3 scripts/codex-guard validate --include-untracked` prior to committing.
- Outstanding risks/todos: finalize guard coverage + regression suite.

## Conflict & Scope Declaration
- Related plans: plan_compliance_phase1_20250925 (enforcement baseline).
- Guard cross-check: ensure `git diff --name-only` remains within listed scope.

## Evidence Checklist
- Store guard logs under `reports/session-continuation/guard-<timestamp>.txt`.
- Store pytest outputs under `reports/session-continuation/tests-<timestamp>.txt`.
- Update tracker + session logs with S:W:H:E formatted entries per guard policy.

## Emergency Bypass Protocol
- No bypass authorized; keep `plan-step-emergency` as `n/a` unless waiver granted.

## Completion
- When plan steps complete and evidence captured, mark tracker checklist items and archive plan (link from `plans/archive/`).
