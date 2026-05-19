---
session_id: {{session_id}}
work_context: {{work_context}}
handler_target: {{current_work_rel}}
task_ids: [{{task_id}}]
branch_policy: feature-required
evidence_summary:
  - {{work_rel}}/
  - {{current_work_rel}}
  - {{session_rel}}
  - {{plan_rel}}
plan_version: v1
emergency_bypass: false
---

# Plan - Task {{task_id}} {{title}}

## Header
- **Session ID (S)**: {{session_id}}
- **Work Context (W)**: {{work_context}}
- **Handler Target (H)**: {{current_work_rel}}
- **Task IDs**: {{task_id}}
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: {{work_rel}}/, {{current_work_rel}}, {{session_rel}}, {{plan_rel}}
- **Plan Version**: v1
- **Emergency Bypass**: false
- **Authority**: Aegis-native workflow state (`{{current_work_rel}}`)
- **Optional Integrations**: Taskmaster and Serena may be used when present, but are not required for READY unless this task marks them required.

## Plan Table
| Step ID | Description | Evidence | Status |
| --- | --- | --- | --- |
| plan-step-scope | Confirm task scope, constraints, expected outputs, and affected files before implementation | {{work_rel}}/FINDINGS.md; {{work_rel}}/DECISIONS.md | in-progress |
| plan-step-implement | Make only task-scoped changes and record implementation notes | {{work_rel}}/IMPLEMENTATION.md; changed files | pending |
| plan-step-verify | Run verification, capture reports, and update handoff state | {{reports_rel}}/; {{work_rel}}/HANDOFF.md; {{tracker_rel}} | pending |
| plan-step-emergency | Optional - only if a bypass is explicitly authorized | Waiver plus post-mortem note in DECISIONS.md and FINDINGS.md | n/a |

## Scope
- `{{current_work_rel}}`
- `{{session_rel}}`
- `{{plan_rel}}`
- `{{work_rel}}/`
- `{{reports_rel}}/`
- Task {{task_id}} only

## Goals
{{goals_checklist}}

## Branch Policy
- Working branch: `{{branch_current}}`
- Persistent work should happen on a branch containing `task-{{task_id}}`.

## Amendments & Versioning
- {{date}} - Task {{task_id}} kickoff created by Aegis.

## Continuation & Handoff
- Next owner: project owner
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read `{{current_work_rel}}`.
  3. Read `{{tracker_rel}}` and `{{work_rel}}/HANDOFF.md`.
  4. Run Aegis readiness/verify commands before mutation.
- Outstanding risks/todos: keep Taskmaster and Serena optional unless explicitly enabled for this task.

## Conflict & Scope Declaration
- Related plans: none recorded at kickoff.
- Gate cross-check: Aegis readiness must stay aligned with the task branch, current session, current plan, active work-tracking folder, and `{{current_work_rel}}`.

## Evidence Checklist
- [x] Aegis current work state exists
- [x] Session and plan current pointers exist
- [x] Active work-tracking folder exists
- [ ] Scope notes recorded before implementation
- [ ] Implementation notes recorded after changes
- [ ] Verification evidence stored under `{{reports_rel}}/`
- [ ] Handoff updated before closeout
- Progress entries must use `[S:{{session_id}}|W:{{work_context}}|H:<handler>|E:<evidence>]` so session, work, handler, and evidence are traceable.

## Emergency Bypass Protocol
- No bypass authorized.
- Any bypass must be explicitly authorized by the user, recorded in DECISIONS.md, and followed by verification evidence.
