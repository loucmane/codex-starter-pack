---
session_id: 2026-04-24-003
work_context: task96-interactive-template-wizard
handler_target: docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-wizard-draft.md
task_ids: [96]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/
  - docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-wizard-draft.md
  - scripts/codex-task
  - tests/meta_workflow_guard/test_codex_task.py
  - .taskmaster/tasks/task_096.txt
plan_version: v1
emergency_bypass: false
---

# Plan - Task 96 Interactive Template Wizard

## Header
- **Session ID (S)**: 2026-04-24-003
- **Work Context (W)**: task96-interactive-template-wizard
- **Handler Target (H)**: docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-wizard-draft.md
- **Task IDs**: 96
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/, docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-wizard-draft.md, scripts/codex-task, tests/meta_workflow_guard/test_codex_task.py, .taskmaster/tasks/task_096.txt
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary against the current helper surface | docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard kickoff flow, helper integration, and usage documentation | scripts/codex-task; tests/meta_workflow_guard/test_codex_task.py; templates/TOOLS.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/`
- `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-wizard-draft.md`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `templates/TOOLS.md`
- `templates/workflows/taskmaster/work-tracking-enforcement.md`
- Taskmaster Task `96`

## Branch Policy
- Working branch: `feat/task-96-interactive-template-wizard`

## Amendments & Versioning
- 2026-04-24 - Task 96 kickoff after Task 95 merge and archive.
- 2026-04-24 - Scope decision: implement the first wizard slice as `codex-task wizard kickoff` on top of the existing helper commands rather than as a separate CLI.
- 2026-04-24 - Implementation completed: wizard kickoff scaffolds session, plan, active work tracking, session state, Taskmaster status, and initial plan sync.
- 2026-04-24 - Verification completed: wizard tests passed, help output captured, plan sync passed, guard passed, and Taskmaster shows Task 96 plus subtasks 96.1-96.5 as done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 96 and subtasks `96.1` through `96.5`.
  3. Re-read `designs/wizard-flow.md` before extending the wizard beyond kickoff.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard constrained to deterministic helper flows; richer multi-step or multi-template orchestration belongs in later work if needed.

## Conflict & Scope Declaration
- Related plans: Task 95 drift detection, Task 97 metrics dashboard.
- Guard cross-check: wizard flows must preserve branch policy, session state, plan sync, and active-folder compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Session/tracker entries for kickoff, implementation, and docs
- Wizard-specific regression tests
- Final plan sync and guard logs under the Task 96 reports folder

## Emergency Bypass Protocol
- No bypass authorized.
