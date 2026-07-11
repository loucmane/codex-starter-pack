---
session_id: 2026-07-11-001
work_context: task236-aegis-usability-convergence-roadmap
handler_target: docs/aegis/aegis-usability-convergence-roadmap.md
task_ids: [236]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/
  - docs/aegis/aegis-usability-convergence-roadmap.md
  - docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/reports/aegis-usability-convergence/current-dogfood-snapshot.md
  - .serena/memories/2026-07-11_task236_aegis_usability_convergence_roadmap.md
  - .taskmaster/tasks/task_236.md
  - .taskmaster/tasks/tasks.json
plan_version: v1
emergency_bypass: false
---

# Plan - Task 236 Define Aegis usability convergence roadmap

## Header
- **Session ID (S)**: 2026-07-11-001
- **Work Context (W)**: task236-aegis-usability-convergence-roadmap
- **Handler Target (H)**: docs/aegis/aegis-usability-convergence-roadmap.md
- **Task IDs**: 236
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/, docs/aegis/aegis-usability-convergence-roadmap.md, docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/reports/aegis-usability-convergence/current-dogfood-snapshot.md, .serena/memories/2026-07-11_task236_aegis_usability_convergence_roadmap.md, .taskmaster/tasks/task_236.md, .taskmaster/tasks/tasks.json
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Ground the convergence scope in capsule, parity-matrix, HP-Fetcher, Blog, worktree, output-budget, and installer evidence | docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/DECISIONS.md; docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/reports/aegis-usability-convergence/current-dogfood-snapshot.md | completed |
| plan-step-implement | Write the planning-only program document, create independently deliverable Taskmaster tasks, and gate Task 210 on required evidence | docs/aegis/aegis-usability-convergence-roadmap.md; .taskmaster/tasks/tasks.json; .taskmaster/tasks/task_236.md; .taskmaster/tasks/task_237.md; .taskmaster/tasks/task_238.md; .taskmaster/tasks/task_239.md; .taskmaster/tasks/task_240.md; .taskmaster/tasks/task_241.md; .taskmaster/tasks/task_242.md; .taskmaster/tasks/task_243.md; .taskmaster/tasks/task_244.md; .taskmaster/tasks/task_210.md | completed |
| plan-step-verify | Validate the full Taskmaster graph, plan/tracker parity, guards, task scope, and handoff state | docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/reports/aegis-usability-convergence/task-verification.md; docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260711-task236-aegis-usability-convergence-roadmap-ACTIVE/`
- `docs/aegis/aegis-usability-convergence-roadmap.md`
- `.serena/memories/2026-07-11_task236_aegis_usability_convergence_roadmap.md`
- `.taskmaster/tasks/tasks.json`
- `.taskmaster/tasks/task_236.md`
- generated task files for the convergence tasks
- Task 244 source-checkout closeout compatibility task
- Task 210 dependency metadata and generated task file
- Taskmaster Task `236`

## Branch Policy
- Working branch: `feat/task-236-aegis-usability-convergence-roadmap`

## Amendments & Versioning
- 2026-07-11 - Task 236 kickoff created via the guided wizard flow.
- 2026-07-11 - Corrected the generic wizard plan to the owner-approved planning-only convergence scope; no runtime implementation is authorized in Task 236.
- 2026-07-11 - Added Task 244 after live closeout proved the upstream source checkout cannot resolve its completed archive without installed target state.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 236 and its subtasks.
  3. Review the convergence roadmap and current dogfood snapshot before changing the Taskmaster graph.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: do not infer worktree capture failure from ledger counts alone; separate asset presence, hook activation, shared-store resolution, and attribution before implementing a fix.

## Conflict & Scope Declaration
- Related plans: Tasks 208, 210, 229, 233, 234, and 235.
- Gate cross-check: Task 210 must remain blocked on every convergence task that supplies required parity evidence; this task may plan and update dependencies but may not retire a legacy surface.

## Evidence Checklist
- Dated dogfood snapshot under `reports/aegis-usability-convergence/`
- Convergence program under `docs/aegis/`
- Supported Taskmaster mutations and targeted generated task files
- Full-graph Taskmaster health and dependency validation
- Plan/tracker parity, work-tracking audit, guard, and diff evidence

## Emergency Bypass Protocol
- No bypass authorized.
