---
session_id: 2026-04-24-006
work_context: task99-portable-foundation-spec
handler_target: templates/metadata/template-metadata-policy.json
task_ids: [99]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/
  - templates/metadata/template-metadata-policy.json
  - .taskmaster/tasks/task_099.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 99 Portable Foundation Specification

## Header
- **Session ID (S)**: 2026-04-24-006
- **Work Context (W)**: task99-portable-foundation-spec
- **Handler Target (H)**: templates/metadata/template-metadata-policy.json
- **Task IDs**: 99
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/, templates/metadata/template-metadata-policy.json, .taskmaster/tasks/task_099.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the specification inputs, boundaries, and section outline for the portable foundation contract | docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/designs/portable-foundation-spec-outline.md | completed |
| plan-step-implement | Draft the canonical portable foundation specification and link it into the engine reference set | templates/engine/core/portable-foundation-spec.md; templates/engine/README.md; docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status for Task 99 | docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/reports/portable-foundation-spec/; docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/`
- `templates/metadata/template-metadata-policy.json`
- `templates/engine/core/portable-foundation-spec.md`
- `templates/engine/README.md`
- `docs/ai/work-tracking/archive/20260424-task98-externalize-repo-structure-config-COMPLETED/designs/repo-structure-config-contract.md`
- `templates/workflows/taskmaster/alignment.md`
- `templates/workflows/taskmaster/work-tracking-enforcement.md`
- `.taskmaster/tasks/task_099.txt`
- Taskmaster Task `99`

## Branch Policy
- Working branch: `feat/task-99-portable-foundation-spec`

## Amendments & Versioning
- 2026-04-24 - Task 99 kickoff created via the guided wizard flow.
- 2026-04-24 - Replaced the generic kickoff scope with the portable-foundation specification outline and canonical spec target.
- 2026-04-24 - Completed the scope and implementation phases after drafting the canonical specification and linking it into the engine reference set.
- 2026-04-24 - Completed verification after passing guard, storing evidence, and marking Taskmaster Task 99 done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 99 and its implementation details.
  3. Review the specification outline, Task 91 metadata model, and Task 98 repo-structure contract.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the specification clear about what belongs in portable core logic versus repo-local adapter configuration.

## Conflict & Scope Declaration
- Related plans: Task 91 metadata portability, Task 98 repo-structure configuration, and follow-on portability Tasks 100-102.
- Guard cross-check: the specification must describe the current enforceable behavior accurately enough that follow-on bootstrap/migration work can use it as a contract.

## Evidence Checklist
- Specification outline under `designs/`
- Canonical portable foundation spec under `templates/engine/core/`
- Tracker/session entries for scope, drafting, and verification progress
- Stored guard/Taskmaster evidence once the specification draft is finalized

## Emergency Bypass Protocol
- No bypass authorized.
