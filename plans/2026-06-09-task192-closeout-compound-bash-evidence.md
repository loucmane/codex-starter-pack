---
session_id: 2026-06-09-003
work_context: task192-closeout-compound-bash-evidence
handler_target: .taskmaster/tasks/task_192.md
task_ids: [192]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/
  - .taskmaster/tasks/task_192.md
  - .taskmaster/tasks/task_192.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 192 Closeout must normalize compound Bash evidence

## Header
- **Session ID (S)**: 2026-06-09-003
- **Work Context (W)**: task192-closeout-compound-bash-evidence
- **Handler Target (H)**: .taskmaster/tasks/task_192.md
- **Task IDs**: 192
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/, .taskmaster/tasks/task_192.md, .taskmaster/tasks/task_192.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Diagnose the HP-Coach closeout evidence-fragment failure and define the safe normalization boundary | docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/designs/compound-bash-evidence-normalization.md | completed |
| plan-step-implement | Implement markdown-aware closeout evidence tokenization/matching and mirror it into packaged assets | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; tests/meta_workflow_guard/test_aegis_installer.py; docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused pytest/ruff evidence and confirm closeout/handoff regressions pass | docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/reports/closeout-compound-bash-evidence/verification.md; docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260609-task192-closeout-compound-bash-evidence-ACTIVE/`
- `.taskmaster/tasks/task_192.md`
- `.taskmaster/tasks/task_192.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `192`

## Branch Policy
- Working branch: `feat/task-192-closeout-compound-bash-evidence`

## Amendments & Versioning
- 2026-06-09 - Task 192 kickoff created via the guided wizard flow.
- 2026-06-09 - Re-scoped plan rows from generic wizard wording to compound Bash closeout evidence normalization and marked scope/implementation/verification complete.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 192 and its subtasks.
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
