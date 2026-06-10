---
session_id: 2026-06-10-003
work_context: task203-capsule-record-hooks
handler_target: .taskmaster/tasks/task_203.md
task_ids: [203]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/
  - .taskmaster/tasks/task_203.md
  - .taskmaster/tasks/task_203.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 203 Capsule PR-1b: async record hooks

## Header
- **Session ID (S)**: 2026-06-10-003
- **Work Context (W)**: task203-capsule-record-hooks
- **Handler Target (H)**: .taskmaster/tasks/task_203.md
- **Task IDs**: 203
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/, .taskmaster/tasks/task_203.md, .taskmaster/tasks/task_203.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-1b boundary from AEGIS_CAPSULE_SPEC.md sections 1.1, 1.2, and 2: the five touchpoints, recorder design (one gate_lib record command, always-exit-0), event classification, payload-fixture prerequisite, hygiene rider, out-of-scope list | docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/designs/record-hooks-scope.md | completed |
| plan-step-implement | Capture live hook payload fixtures, then implement ledger-record.sh, gate_lib record routing, exec-form async settings entries, aegis hook dispatcher additions, manifest managed_files, recorder classification (mutation/tool_failure/delivery/task_truth), and the .gitignore hygiene rider | aegis_foundation/cli.py; docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Run fixture-driven recorder tests + renderer/dispatcher/manifest tests + full suite and guard stack; store evidence under reports/capsule-record-hooks/ and refresh handoff | docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task203-capsule-record-hooks-ACTIVE/`
- `aegis_foundation/assets/.claude/scripts/` (ledger-record.sh, gate_lib.py) + live mirrors
- `scripts/_aegis_installer.py` + assets mirror (settings renderer, manifest, hygiene rider)
- `aegis_foundation/cli.py` (hook dispatcher choices)
- `tests/claude_adapter/`, `tests/meta_workflow_guard/`, `tests/fixtures/hook_payloads/`
- `.taskmaster/tasks/` (task 203)
- Taskmaster Task `203`

## Branch Policy
- Working branch: `feat/task-203-capsule-record-hooks`

## Amendments & Versioning
- 2026-06-10 - Task 203 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 203 and its subtasks.
  3. Read AEGIS_CAPSULE_SPEC.md sections 1.1/2 and designs/record-hooks-scope.md before changing hook wiring.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: recorder must always exit 0 (never block); existing synchronous hooks untouched until PR-4; SessionStart/SessionEnd fixtures may be gap-documented.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
