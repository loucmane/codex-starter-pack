---
session_id: 2026-07-13-004
work_context: task248-codex-hook-adapter
handler_target: .claude/scripts/gate_lib.py
task_ids: [248]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/
  - .claude/scripts/gate_lib.py
  - .taskmaster/tasks/task_248.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 248 Implement First-Class Codex Hook Adapter

## Header
- **Session ID (S)**: 2026-07-13-004
- **Work Context (W)**: task248-codex-hook-adapter
- **Handler Target (H)**: .claude/scripts/gate_lib.py
- **Task IDs**: 248
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/, .claude/scripts/gate_lib.py, .taskmaster/tasks/task_248.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the canonical Codex hook, parser, policy, evidence, installer, trust, and rollout contract | docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/designs/codex-hook-adapter-scope.md | completed |
| plan-step-implement | Implement first-class apply_patch handling and the managed Codex adapter with source/package parity | .claude/scripts/gate_lib.py; aegis_foundation/assets/.claude/scripts/gate_lib.py; scripts/_aegis_installer.py; docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260713-task248-codex-hook-adapter-ACTIVE/`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/.codex/hooks.json`
- `docs/aegis/agent-adapter-contract.md`
- `aegis_foundation/assets/docs/aegis/agent-adapter-contract.md`
- `.taskmaster/tasks/task_248.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `248`

## Branch Policy
- Working branch: `feat/task-248-codex-hook-adapter-bootstrap`

## Amendments & Versioning
- 2026-07-13 - Task 248 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 248 and its subtasks.
  3. Review the canonical Codex hook adapter scope before changing runtime or installer behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve existing Claude behavior, inspect all paths atomically, fail closed on parser faults, and never bypass Codex hook trust.

## Conflict & Scope Declaration
- Related plans: Tasks 202-205 passive ledger/gate work, Task 237 mode-aware guidance, Task 239 worktree evidence, and Task 247 autonomous delivery.
- Guard cross-check: the Codex adapter must reuse the existing Aegis workflow and evidence model rather than introduce a parallel control plane.

## Evidence Checklist
- Canonical Codex hook adapter scope under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
