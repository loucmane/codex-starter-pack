---
session_id: 2026-06-12-002
work_context: task212-coldstart-falsifier-v2
handler_target: aegis_foundation/replay_coldstart.py
task_ids: [212]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/
  - aegis_foundation/replay_coldstart.py
  - .taskmaster/tasks/task_212.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 212 Cold-start falsifier v2: recon-to-decision metric + READY-envelope scenarios

## Header
- **Session ID (S)**: 2026-06-12-002
- **Work Context (W)**: task212-coldstart-falsifier-v2
- **Handler Target (H)**: aegis_foundation/replay_coldstart.py
- **Task IDs**: 212
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/, aegis_foundation/replay_coldstart.py, .taskmaster/tasks/task_212.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Cold-start falsifier v2: recon-to-decision metric + READY-envelope scenarios | docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Cold-start falsifier v2: recon-to-decision metric + READY-envelope scenarios | scripts/codex-task; docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/`
- `aegis_foundation/replay_coldstart.py`
- `.taskmaster/tasks/task_212.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `212`

## Branch Policy
- Working branch: `feat/task-212-coldstart-falsifier-v2`

## Amendments & Versioning
- 2026-06-12 - Task 212 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 212 and its subtasks.
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
