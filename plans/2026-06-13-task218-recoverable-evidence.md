---
session_id: 2026-06-13-003
work_context: task218-recoverable-evidence
handler_target: scripts/_aegis_installer.py
task_ids: [218]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_218.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 218 Robust + recoverable closeout evidence (stable-key matching)

## Header
- **Session ID (S)**: 2026-06-13-003
- **Work Context (W)**: task218-recoverable-evidence
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 218
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_218.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Robust + recoverable closeout evidence (stable-key matching) | docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Robust + recoverable closeout evidence (stable-key matching) | scripts/codex-task; docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_218.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `218`

## Branch Policy
- Working branch: `feat/task-218-recoverable-evidence`

## Amendments & Versioning
- 2026-06-13 - Task 218 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 218 and its subtasks.
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
