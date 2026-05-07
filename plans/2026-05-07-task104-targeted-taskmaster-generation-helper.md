---
session_id: 2026-05-07-001
work_context: task104-targeted-taskmaster-generation-helper
handler_target: scripts/codex-task
task_ids: [104]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/
  - scripts/codex-task
  - tests/
  - templates/
  - .taskmaster/tasks/task_104.txt
plan_version: v1
emergency_bypass: false
---

# Plan - Task 104 Targeted Taskmaster Task-File Generation Helper

## Header
- **Session ID (S)**: 2026-05-07-001
- **Work Context (W)**: task104-targeted-taskmaster-generation-helper
- **Handler Target (H)**: scripts/codex-task
- **Task IDs**: 104
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/, scripts/codex-task, tests/, templates/, .taskmaster/tasks/task_104.txt
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---------|-------------|----------|--------|
| plan-step-scope | Design the targeted Taskmaster generation helper, including Taskmaster `0.43.1` `.md` output behavior, `.txt` compatibility, and safeguards for unrelated task files | docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/designs/targeted-taskmaster-generation.md | completed |
| plan-step-implement | Implement `python3 scripts/codex-task taskmaster generate-one --id <task-id>` and update kickoff/status workflows to use targeted generation instead of broad in-place generation | scripts/codex-task; tests/; docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused regression evidence, guard/pre-commit evidence, Taskmaster evidence, and final handoff notes | docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/reports/targeted-taskmaster-generation-helper/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `scripts/codex-task`
- `tests/`
- `templates/TOOLS.md`
- `templates/workflows/taskmaster/`
- `templates/engine/validation/foundation-adoption-guide.md`
- `.taskmaster/tasks/task_104.txt`
- `docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/`
- `sessions/2026/05/2026-05-07-001-task104-targeted-taskmaster-generation-helper.md`

## Branch Policy
- Working branch: `feat/task-104-targeted-taskmaster-generation-helper`

## Amendments & Versioning
- 2026-05-07 - Manual kickoff used because the existing wizard path invokes broad `task-master generate`, which Task 104 is intended to replace.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 104 and `.taskmaster/tasks/task_104.txt`.
  3. Review `designs/targeted-taskmaster-generation.md` before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: after PR merge, archive the Task 104 work-tracking folder and close the session into between-session state.

## Conflict & Scope Declaration
- Related plans: Task 103 Claude adapter closeout, Task 9 Git hooks infrastructure, Task 5 `codex-task` CLI, Task 104 Taskmaster generation helper.
- Guard cross-check: Task 104 work must preserve feature-branch, session/current, plans/current, tracker, and plan-sync compliance while avoiding broad generated task-file drift.

## Evidence Checklist
- Targeted generation design under `designs/`
- Unit/regression tests showing unrelated task files are not dirtied
- Guard, pre-commit, audit, plan-sync, diff-check, and Taskmaster evidence under `reports/targeted-taskmaster-generation-helper/`
- Taskmaster Task 104 status and task file updated without broad in-place generation cleanup

## Emergency Bypass Protocol
- No bypass authorized.
