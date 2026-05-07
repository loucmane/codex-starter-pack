---
session_id: 2026-05-07-003
work_context: task106-claude-runtime-smoke-test
handler_target: .taskmaster/tasks/task_106.md
task_ids: [106]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/
  - docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/designs/smoke-test-protocol.md
  - docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/phase1-cold-session-2026-05-07.md
  - docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/phase2-ready-session-2026-05-07.md
  - docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/final-verification-2026-05-07.md
  - .taskmaster/tasks/task_106.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 106 Smoke Test Claude Runtime Adapter In Harness

## Header
- **Session ID (S)**: 2026-05-07-003
- **Work Context (W)**: task106-claude-runtime-smoke-test
- **Handler Target (H)**: .taskmaster/tasks/task_106.md
- **Task IDs**: 106
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/, docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/designs/smoke-test-protocol.md, docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/phase1-cold-session-2026-05-07.md, docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/phase2-ready-session-2026-05-07.md, docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/final-verification-2026-05-07.md, .taskmaster/tasks/task_106.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the two-phase Claude harness smoke-test protocol, expected gate behavior, and evidence targets | docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/designs/smoke-test-protocol.md | completed |
| plan-step-implement | Run the cold-session and READY-state Claude harness prompts, then capture observed behavior | docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/phase1-cold-session-2026-05-07.md; docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/phase2-ready-session-2026-05-07.md | completed |
| plan-step-verify | Store final evidence, refresh handoff docs, run plan sync/audit/guard, and confirm Taskmaster status | docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/reports/claude-runtime-smoke-test/final-verification-2026-05-07.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260507-task106-claude-runtime-smoke-test-ACTIVE/`
- `.taskmaster/tasks/task_106.md`
- `.claude/scripts/pretooluse-gate.sh`
- `.claude/scripts/readiness.sh`
- `.claude/scripts/codex-path-guard.sh`
- `.claude/scripts/bash-command-guard.sh`
- `tests/`
- Taskmaster Task `106`

## Branch Policy
- Working branch: `feat/task-106-claude-runtime-smoke-test`

## Amendments & Versioning
- 2026-05-07 - Task 106 kickoff created via the guided wizard flow.
- 2026-05-07 - Plan corrected from generic wizard wording to the actual Claude runtime smoke-test protocol after Phase 1 evidence was recorded.
- 2026-05-07 - Phase 2 READY-state evidence recorded; plan-step-implement completed.
- 2026-05-07 - Final verification evidence recorded; plan-step-verify completed.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 106 and its subtasks.
  3. Review `designs/smoke-test-protocol.md` before running additional Claude harness prompts.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: prepare commit/PR handoff, then archive the active folder after PR merge.

## Conflict & Scope Declaration
- Related plans: Tasks 103 and 105 Claude adapter hardening work.
- Guard cross-check: Task 106 must distinguish cold-session readiness blocking from READY-state protected-path blocking.

## Evidence Checklist
- Smoke-test protocol under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored Phase 1 and Phase 2 Claude harness evidence

## Emergency Bypass Protocol
- No bypass authorized.
