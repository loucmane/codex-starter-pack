---
session_id: 2026-05-26-002
work_context: task125-public-aegis-adoption-flow
handler_target: aegis_foundation/cli.py
task_ids: [125]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/
  - aegis_foundation/cli.py
  - .taskmaster/tasks/task_125.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 125 Build Public Aegis Real-Project Adoption Flow

## Header
- **Session ID (S)**: 2026-05-26-002
- **Work Context (W)**: task125-public-aegis-adoption-flow
- **Handler Target (H)**: aegis_foundation/cli.py
- **Task IDs**: 125
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/, aegis_foundation/cli.py, .taskmaster/tasks/task_125.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Build Public Aegis Real-Project Adoption Flow | docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Build Public Aegis Real-Project Adoption Flow | scripts/codex-task; docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/reports/public-flow/initial-public-flow-smoke.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/reports/public-flow/normal-language-claude-live-acceptance.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/`
- `aegis_foundation/cli.py`
- `.taskmaster/tasks/task_125.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `125`

## Branch Policy
- Working branch: `feat/task-125-public-aegis-adoption-flow`

## Amendments & Versioning
- 2026-05-26 - Task 125 kickoff created via the guided wizard flow.
- 2026-05-26 - Scope completed with public adoption flow boundary and acceptance shape.
- 2026-05-27 - Public init/start implementation and normal-language Claude live acceptance evidence completed.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 125 and its subtasks.
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
