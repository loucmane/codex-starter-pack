---
session_id: 2026-06-09-002
work_context: task184-completed-observation-terminal
handler_target: .claude/scripts/readiness.sh
task_ids: [184]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/
  - .claude/scripts/readiness.sh
  - .taskmaster/tasks/task_184.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 184 Treat completed Aegis observations as terminal state

## Header
- **Session ID (S)**: 2026-06-09-002
- **Work Context (W)**: task184-completed-observation-terminal
- **Handler Target (H)**: .claude/scripts/readiness.sh
- **Task IDs**: 184
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/, .claude/scripts/readiness.sh, .taskmaster/tasks/task_184.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define terminal completed-observation behavior for readiness, next guidance, and repeated stop | docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Update readiness, next guidance, and observe-stop idempotence for completed observations | .claude/scripts/readiness.sh; scripts/_aegis_installer.py; aegis_foundation/assets/.claude/scripts/readiness.sh; aegis_foundation/assets/scripts/_aegis_installer.py; docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Cover completed observation terminal state and preserve mutation blocking until kickoff | tests/meta_workflow_guard/test_aegis_installer.py; docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260609-task184-completed-observation-terminal-ACTIVE/`
- `.claude/scripts/readiness.sh`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_184.md`
- `tests/`
- Taskmaster Task `184`

## Branch Policy
- Working branch: `feat/task-184-completed-observation-terminal`

## Amendments & Versioning
- 2026-06-09 - Task 184 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 184 and its subtasks.
  3. Review the terminal-observation behavior before changing readiness or next guidance.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: completed observation must not grant arbitrary mutation readiness on `main`; it should fall back to normal kickoff/task binding.

## Conflict & Scope Declaration
- Related plans: Tasks 180-183 observation-mode and recovery hardening.
- Guard cross-check: completed observation is terminal, in-progress observation remains READY for observation tooling, and normal mutations still require kickoff.

## Evidence Checklist
- Decision note documenting terminal observation semantics
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence for the completed-observation fix

## Emergency Bypass Protocol
- No bypass authorized.
