---
session_id: 2026-05-04-001
work_context: task6-codex-guard-validation-tool
handler_target: docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/TRACKER.md
task_ids: [6]
branch_policy: feature-required
evidence_summary:
  - sessions/2026/05/2026-05-04-001-task4-merge-cleanup-task5-kickoff.md
  - docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/
  - .taskmaster/tasks/task_006.txt
  - scripts/codex-guard
plan_version: v1
emergency_bypass: false
---

# Plan - Task 6 Codex-Guard Validation Tool

## Header
- **Session ID (S)**: 2026-05-04-001
- **Work Context (W)**: task6-codex-guard-validation-tool
- **Handler Target (H)**: docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/TRACKER.md
- **Task IDs**: 6
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: sessions/2026/05/2026-05-04-001-task4-merge-cleanup-task5-kickoff.md, docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/, .taskmaster/tasks/task_006.txt, scripts/codex-guard
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---------|-------------|----------|--------|
| plan-step-scope | Confirm Task 6 kickoff boundary, branch policy, and scope-reconciliation-first rule | sessions/2026/05/2026-05-04-001-task4-merge-cleanup-task5-kickoff.md; docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/TRACKER.md; .taskmaster/tasks/task_006.txt | completed |
| plan-step-scope-audit | Reconcile Task 6 wording against the current `scripts/codex-guard` implementation and identify the real gap | docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/designs/task6-scope-audit.md; docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/FINDINGS.md; scripts/codex-guard | completed |
| plan-step-implement | Implement only the proven current-state Task 6 gap with tests/evidence | .pre-commit-config.yaml; tests/meta_workflow_guard/test_guard_rules.py; templates/TOOLS.md; templates/engine/enforcement/meta-workflow-guard-ci-plan.md | completed |
| plan-step-verify | Run focused tests, plan sync, work-tracking audit, guard, and diff check | docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/reports/scope-audit/tests-2026-05-04-final.txt; docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/reports/scope-audit/drift-check-2026-05-04-final.txt; docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/reports/scope-audit/guard-2026-05-04-final.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/HANDOFF.md | n/a |

## Scope
- Review Taskmaster Task 6 and current `scripts/codex-guard`.
- Identify which parts of Task 6 are already complete from later foundation work.
- Choose the smallest valuable remaining gap before implementation.
- Keep all Task 6 work on `feat/task-6-codex-guard-validation-tool`.

## Non-Scope
- Rebuilding `scripts/codex-guard` from scratch.
- Reintroducing stale guard requirements that no longer match the portable foundation.
- Editing tests just to force a pass before proving the current implementation gap.
- Implementing before the current-state audit is recorded.

## Branch Policy
- Working branch: `feat/task-6-codex-guard-validation-tool`.

## Amendments & Versioning
- 2026-05-04 - Created Task 6 plan after Task 5 merge cleanup and archive.
- 2026-05-04 - Completed scope audit and implemented local pre-commit guard wiring as the proven Task 6 gap.
- 2026-05-04 - Completed focused tests and Taskmaster closeout.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current`, this plan, and the Task 6 work-tracking folder.
  2. Read Taskmaster Task 6 and current `scripts/codex-guard`.
  3. Complete scope reconciliation before implementing anything.
- Outstanding risks/todos: Review/push Task 6 branch, then open/merge PR. After merge, archive Task 6 and start Task 8.

## Emergency Bypass Protocol
- No bypass authorized.
