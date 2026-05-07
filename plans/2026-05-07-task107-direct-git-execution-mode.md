---
session_id: 2026-05-07-004
work_context: task107-direct-git-execution-mode
handler_target: .taskmaster/tasks/task_107.md
task_ids: [107]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/
  - docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/designs/direct-git-execution-scope.md
  - docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/reports/direct-git-execution-mode/verification-2026-05-07.md
  - .taskmaster/tasks/task_107.md
  - templates/conventions/git/commit-format.md
  - scripts/codex-guard
plan_version: v1
emergency_bypass: false
---

# Plan - Task 107 Enforce Direct Git Execution Mode

## Header
- **Session ID (S)**: 2026-05-07-004
- **Work Context (W)**: task107-direct-git-execution-mode
- **Handler Target (H)**: .taskmaster/tasks/task_107.md
- **Task IDs**: 107
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/, docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/designs/direct-git-execution-scope.md, docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/reports/direct-git-execution-mode/verification-2026-05-07.md, .taskmaster/tasks/task_107.md, templates/conventions/git/commit-format.md, scripts/codex-guard
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define direct Git execution policy, response modes, and stale GAC-default conflict | docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/designs/direct-git-execution-scope.md | completed |
| plan-step-implement | Update commit workflow templates and guard coverage so direct Git/GitHub execution is the default | templates/conventions/git/commit-format.md; templates/behaviors/git/before-commit.md; templates/handlers/operators/git/create-commit-message.md; scripts/codex-guard; tests/meta_workflow_guard/test_guard_rules.py | completed |
| plan-step-verify | Store evidence, refresh handoff docs, run validation, and confirm Taskmaster status | docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/reports/direct-git-execution-mode/verification-2026-05-07.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/`
- `.taskmaster/tasks/task_107.md`
- `templates/conventions/git/commit-format.md`
- `templates/behaviors/git/before-commit.md`
- `templates/handlers/operators/git/create-commit-message.md`
- `templates/TOOLS.md`
- `templates/tools/git/commands.md`
- `scripts/codex-guard`
- `tests/meta_workflow_guard/test_guard_rules.py`
- Taskmaster Task `107`

## Branch Policy
- Working branch: `feat/task-107-direct-git-execution-mode`

## Amendments & Versioning
- 2026-05-07 - Task 107 kickoff created via the guided wizard flow.
- 2026-05-07 - Plan corrected from generic wizard wording to direct Git execution enforcement scope.
- 2026-05-07 - Template and guard implementation completed; plan-step-implement marked complete.
- 2026-05-07 - Final validation passed and plan-step-verify marked complete.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 107 and its subtasks.
  3. Review `designs/direct-git-execution-scope.md` before changing commit workflow guidance.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: commit, push, open PR, and archive after merge.

## Conflict & Scope Declaration
- Related plans: Task 9 Git hooks infrastructure, Task 104 targeted Taskmaster generation helper, Task 106 Claude runtime smoke test.
- Guard cross-check: canonical commit docs must preserve direct Git execution default and reject stale GAC-default language.

## Evidence Checklist
- Direct Git execution scope note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once implementation lands
- Final plan sync, audit, guard, pytest, and diff-check evidence recorded in `verification-2026-05-07.md`

## Emergency Bypass Protocol
- No bypass authorized.
