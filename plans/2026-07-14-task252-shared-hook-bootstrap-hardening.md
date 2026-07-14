---
session_id: 2026-07-14-005
work_context: task252-shared-hook-bootstrap-hardening
handler_target: scripts/_aegis_installer.py
task_ids: [252]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260714-task252-shared-hook-bootstrap-hardening-ACTIVE/
  - scripts/_aegis_installer.py
  - aegis_foundation/cli.py
  - .claude/scripts/gate_lib.py
  - aegis_foundation/managed_update.py
  - tests/meta_workflow_guard/test_codex_hook_bootstrap.py
  - .taskmaster/tasks/task_252.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 252 Harden Shared Codex Hook Bootstrap Against Mutable Runtime Outages

## Header
- **Session ID (S)**: 2026-07-14-005
- **Work Context (W)**: task252-shared-hook-bootstrap-hardening
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 252
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260714-task252-shared-hook-bootstrap-hardening-ACTIVE/, scripts/_aegis_installer.py, aegis_foundation/cli.py, .claude/scripts/gate_lib.py, aegis_foundation/managed_update.py, tests/meta_workflow_guard/test_codex_hook_bootstrap.py, .taskmaster/tasks/task_252.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the shared-hook failure model, stable bootstrap seam, migration boundary, degraded behavior, and rollback | docs/ai/work-tracking/active/20260714-task252-shared-hook-bootstrap-hardening-ACTIVE/designs/shared-hook-bootstrap.md | completed |
| plan-step-implement | Harden managed Codex hook dispatch and update materialization without changing the local untracked hook definition | scripts/_aegis_installer.py; aegis_foundation/managed_update.py; aegis_foundation/cli.py; .claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260714-task252-shared-hook-bootstrap-hardening-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove bounded failure, exact migration, source/package parity, multi-project isolation, and normal installer behavior | tests/meta_workflow_guard/test_codex_hook_bootstrap.py; docs/ai/work-tracking/active/20260714-task252-shared-hook-bootstrap-hardening-ACTIVE/reports/shared-hook-bootstrap/verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260714-task252-shared-hook-bootstrap-hardening-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/managed_update.py`
- `aegis_foundation/assets/`
- `.taskmaster/tasks/task_252.md`
- `.taskmaster/tasks/task_243.md`
- `tests/meta_workflow_guard/test_codex_hook_bootstrap.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `docs/aegis/`
- Taskmaster Task `252`

## Branch Policy
- Working branch: `feat/task-252-shared-hook-bootstrap-hardening`

## Amendments & Versioning
- 2026-07-14 - Task 252 kickoff created via the guided wizard flow.
- 2026-07-14 - Expanded the implementation evidence surface to include the CLI's target-local dispatch and the live/packaged gate runtime; no local operator hook file entered scope.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 252 and its subtasks.
  3. Review the shared-hook bootstrap design and incident findings before changing dispatch behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve hook stdin and exit semantics, avoid fail-open mutation policy, keep diagnostics bounded, and refuse unknown project-owned hook changes.

## Conflict & Scope Declaration
- Related plans: Tasks 242, 248, and 249 are completed prerequisites; Task 243 consumes this hardening evidence before any parity decision.
- Guard cross-check: generated hooks must remain target-local, source/package assets must agree, exact custom hooks must remain manual review, and no implementation may edit the primary checkout's untracked `.codex/hooks.json`.

## Evidence Checklist
- Shared-hook bootstrap design under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Focused degraded-runtime, installer migration, worktree, and multi-project tests
- Source/package parity plus full guard and verification evidence

## Emergency Bypass Protocol
- No bypass authorized.
