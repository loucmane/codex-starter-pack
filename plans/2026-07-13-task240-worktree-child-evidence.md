---
session_id: 2026-07-13-003
work_context: task240-worktree-child-evidence
handler_target: .claude/scripts/ledger_lib.py
task_ids: [240]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260713-task240-worktree-child-evidence-ACTIVE/
  - .claude/scripts/ledger_lib.py
  - .claude/scripts/gate_lib.py
  - .claude/scripts/witness_lib.py
  - aegis_foundation/replay.py
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_240.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 240 Make Worktree And Child-Agent Evidence First-Class

## Header
- **Session ID (S)**: 2026-07-13-003
- **Work Context (W)**: task240-worktree-child-evidence
- **Handler Target (H)**: .claude/scripts/ledger_lib.py
- **Task IDs**: 240
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260713-task240-worktree-child-evidence-ACTIVE/, .claude/scripts/ledger_lib.py, .claude/scripts/gate_lib.py, .claude/scripts/witness_lib.py, aegis_foundation/replay.py, scripts/_aegis_installer.py, .taskmaster/tasks/task_240.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the additive event schema, native-hook capability boundary, query-isolation rules, migration contract, and rollback | docs/ai/work-tracking/active/20260713-task240-worktree-child-evidence-ACTIVE/designs/worktree-child-evidence-contract.md | completed |
| plan-step-implement | Implement context-enriched ledger rows, Codex lifecycle recording, branch-safe witness/replay queries, installer integration, and docs | .claude/scripts/ledger_lib.py; .claude/scripts/gate_lib.py; .claude/scripts/witness_lib.py; aegis_foundation/replay.py; scripts/_aegis_installer.py | completed |
| plan-step-verify | Prove migration, concurrent writers, child ownership, failures, verification isolation, teardown, installed-target parity, and measured coverage | tests/claude_adapter/; tests/meta_workflow_guard/; docs/ai/work-tracking/active/20260713-task240-worktree-child-evidence-ACTIVE/reports/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260713-task240-worktree-child-evidence-ACTIVE/`
- `.claude/scripts/ledger_lib.py`
- `.claude/scripts/gate_lib.py`
- `.claude/scripts/witness_lib.py`
- `aegis_foundation/cli.py`
- `aegis_foundation/replay.py`
- `aegis_foundation/worktree_capture_audit.py`
- `aegis_foundation/assets/`
- `scripts/_aegis_installer.py`
- `docs/aegis/`
- `.taskmaster/tasks/task_240.md`
- `tests/`
- Taskmaster Task `240`

## Branch Policy
- Working branch: `feat/task-240-worktree-child-evidence`

## Amendments & Versioning
- 2026-07-13 - Task 240 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 240 and its subtasks.
  3. Review the worktree/child evidence contract before changing recorder behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: run final-head governance/closeout checks, publish the task branch, and retain explicit degraded results for untrusted hooks, unsupported clients, and ancestry deeper than client-provided identity.

## Conflict & Scope Declaration
- Related plans: Task 239 capture audit, Task 241 quiet witness shipping interface.
- Guard cross-check: runtime and packaged assets must remain byte-identical; installed targets must upgrade without rewriting old rows.

## Evidence Checklist
- Worktree/child evidence contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence in `reports/worktree-child-evidence/task240-coverage-report.md`

## Emergency Bypass Protocol
- No bypass authorized.
