---
session_id: 2026-06-10-001
work_context: task199-aegis-enforce-advisory-mode
handler_target: .taskmaster/tasks/task_199.md
task_ids: [199]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task199-aegis-enforce-advisory-mode-ACTIVE/
  - .taskmaster/tasks/task_199.md
  - .taskmaster/tasks/task_199.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 199 Aegis enforce advisory mode

## Header
- **Session ID (S)**: 2026-06-10-001
- **Work Context (W)**: task199-aegis-enforce-advisory-mode
- **Handler Target (H)**: .taskmaster/tasks/task_199.md
- **Task IDs**: 199
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task199-aegis-enforce-advisory-mode-ACTIVE/, .taskmaster/tasks/task_199.md, .taskmaster/tasks/task_199.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the strict/advisory enforcement-mode boundary and keep strict-as-absent default compatibility | docs/ai/work-tracking/active/20260610-task199-aegis-enforce-advisory-mode-ACTIVE/TRACKER.md | completed |
| plan-step-implement | Implement `aegis enforce`, advisory gate-decision recording, pending mode tagging, and status/doctor/verify surfacing | .claude/scripts/gate_lib.py; scripts/_aegis_installer.py; aegis_foundation/cli.py; scripts/codex-task | completed |
| plan-step-verify | Prove strict default, blocked-state enforce exemption, advisory no-block behavior, stop/posttool tagging, diagnostics, and asset parity | tests/claude_adapter/test_pretooluse_gates.py; tests/meta_workflow_guard/test_aegis_installer.py | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task199-aegis-enforce-advisory-mode-ACTIVE/`
- `.taskmaster/tasks/task_199.md`
- `.taskmaster/tasks/task_199.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `199`

## Branch Policy
- Working branch: `feat/task-199-aegis-enforce-advisory-mode`

## Amendments & Versioning
- 2026-06-10 - Task 199 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 199 and its subtasks.
  3. Review the advisory-mode implementation and tests before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep advisory mode scoped to strict/advisory pause and decision recording; full replay/hash-chain/policy work remains out of scope for this task.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: absent `.aegis/state/enforcement.json` must preserve strict behavior as the default path.

## Evidence Checklist
- Tracker/session entries for kickoff and implementation progress
- Focused direct hook tests for advisory behavior
- Installer diagnostics tests for CLI/status/doctor/verify surfacing
- Asset parity and live CLI smoke evidence

## Emergency Bypass Protocol
- No bypass authorized.
