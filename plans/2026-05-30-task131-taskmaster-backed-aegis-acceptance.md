---
session_id: 2026-05-30-002
work_context: task131-taskmaster-backed-aegis-acceptance
handler_target: docs/aegis/live-acceptance-matrix.md
task_ids: [131]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/
  - docs/aegis/live-acceptance-matrix.md
  - .taskmaster/tasks/task_131.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 131 Validate Taskmaster-Backed Aegis Claude Workflow Acceptance

## Header
- **Session ID (S)**: 2026-05-30-002
- **Work Context (W)**: task131-taskmaster-backed-aegis-acceptance
- **Handler Target (H)**: docs/aegis/live-acceptance-matrix.md
- **Task IDs**: 131
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/, docs/aegis/live-acceptance-matrix.md, .taskmaster/tasks/task_131.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the Taskmaster-backed acceptance contract, target fixture shape, and expected Taskmaster/Aegis ordering | docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/DECISIONS.md; docs/aegis/live-acceptance-matrix.md | completed |
| plan-step-implement | Harden Aegis next-action/MCP/doc guidance so Taskmaster projects prefer task-master next/show plus explicit-id aegis.kickoff, while preserving aegis.start for projects without Taskmaster | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; aegis_mcp/server.py; docs/aegis/; tests/; docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Run regression tests and live Claude MCP Taskmaster-backed acceptance; confirm Aegis closeout/doctor precede Taskmaster done | docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/reports/; docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260530-task131-taskmaster-backed-aegis-acceptance-ACTIVE/`
- `docs/aegis/live-acceptance-matrix.md`
- `docs/aegis/public-adoption-flow.md`
- `docs/aegis/mcp-client-setup.md`
- `.taskmaster/tasks/task_131.md`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_mcp/server.py`
- `tests/`
- Taskmaster Task `131`

## Branch Policy
- Working branch: `feat/task-131-taskmaster-backed-aegis-acceptance`

## Amendments & Versioning
- 2026-05-30 - Task 131 kickoff created via the guided wizard flow.
- 2026-05-30 - Plan corrected from generic wizard wording to Taskmaster-backed Aegis/Claude workflow acceptance.
- 2026-05-30 - Added Taskmaster-backed next-action/start-refusal regressions, hardened installer/MCP guidance, updated docs, and prepared the live Claude fixture.
- 2026-05-30 - Completed final reload-barrier and isolated HPFetcher acceptance evidence; created follow-up Task 132 for read-only Taskmaster MCP discovery hardening.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 131 and its subtasks.
  3. Review Task 130 live acceptance reports and Taskmaster integration behavior before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: Task 132 tracks the remaining read-only Taskmaster MCP discovery carve-out; Task 131 acceptance and closeout evidence is complete.

## Conflict & Scope Declaration
- Related plans: Task 130 normal-language Aegis acceptance, Task 129 doctor/repair/idempotency, Task 12 Taskmaster integration.
- Guard cross-check: Taskmaster-backed flows must preserve plan/tracker/session compliance, pending S:W:H:E tracking, strict verification, closeout, doctor, and targeted Taskmaster generated-file refresh.

## Evidence Checklist
- Taskmaster-backed fixture setup and live report
- Regression tests proving Taskmaster guidance and explicit-id kickoff behavior
- Tracker/session entries for scope, implementation, and verification progress
- Stored test and guard evidence once hardening lands

## Emergency Bypass Protocol
- No bypass authorized.
