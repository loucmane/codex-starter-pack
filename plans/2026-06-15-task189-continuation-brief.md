---
session_id: 2026-06-15-002
work_context: task189-continuation-brief
handler_target: scripts/_aegis_installer.py
task_ids: [189]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/
  - scripts/_aegis_installer.py
  - aegis_foundation/cli.py
  - aegis_foundation/assets/scripts/_aegis_installer.py
  - .taskmaster/tasks/task_189.md
  - tests/
plan_version: v1
emergency_bypass: false
---

# Plan - Task 189 Add agent-ready continuation brief to aegis next

## Header
- **Session ID (S)**: 2026-06-15-002
- **Work Context (W)**: task189-continuation-brief
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 189
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_189.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Re-anchor on the TM 188 continuation contract; confirm residuals #1 (named brief fields) + #3 (concise rendering) are unbuilt and define the per-state brief design (deferring residual #2 to TM 225) | docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Add CONTINUATION_BRIEF_BY_STATE + _continuation_brief, attach continuation_brief to every _workflow_guidance_payload, thread current_task_authority through next_action, add format_next_summary + aegis next --json; mirror assets; add test_continuation_brief.py | scripts/_aegis_installer.py; aegis_foundation/cli.py; docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Full suite + focused brief/contract/parity green; plan sync, work-tracking audit, guard, git diff --check; refresh handoff/changelog; confirm Taskmaster 189 done | docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/reports/task-verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260615-task189-continuation-brief-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_189.md`
- `tests/`
- Taskmaster Task `189`

## Branch Policy
- Working branch: `feat/task-189-continuation-brief`

## Amendments & Versioning
- 2026-06-15 - Task 189 kickoff created via the guided wizard flow.
- 2026-06-15 - Re-scoped plan steps from generic kickoff template to the actual continuation-brief work; added `aegis_foundation/cli.py` and `aegis_foundation/assets/scripts/_aegis_installer.py` to scope (CLI rendering + parity mirror). Residual #2 (doctor-derived safe-repair vs manual-review states) deferred to TM 225.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 189 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
