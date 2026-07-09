---
session_id: 2026-07-09-001
work_context: task233-legacy-shadow-sweh-projection
handler_target: aegis_foundation/legacy_projection.py
task_ids: [233]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260709-task233-legacy-shadow-sweh-projection-ACTIVE/
  - aegis_foundation/legacy_projection.py
  - .taskmaster/tasks/task_233.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 233 Legacy-shadow S:W:H:E projection from passive ledger

## Header
- **Session ID (S)**: 2026-07-09-001
- **Work Context (W)**: task233-legacy-shadow-sweh-projection
- **Handler Target (H)**: aegis_foundation/legacy_projection.py
- **Task IDs**: 233
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260709-task233-legacy-shadow-sweh-projection-ACTIVE/, aegis_foundation/legacy_projection.py, .taskmaster/tasks/task_233.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define legacy-shadow authority, generated markers, event selection, and PR-4 boundaries | docs/aegis/legacy-shadow-sweh-projection-contract.md; docs/aegis/pr-4-replacement-parity-matrix.md | completed |
| plan-step-implement | Implement ledger-to-S:W:H:E projection, agent-scoped reload handling, and read-only ledger access | aegis_foundation/legacy_projection.py; aegis_foundation/cli.py; scripts/_aegis_installer.py; .claude/scripts/ledger_lib.py | completed |
| plan-step-verify | Validate deterministic projection, package mirrors, Taskmaster health, and downstream dogfood | tests/claude_adapter/test_legacy_projection.py; docs/aegis/blog-legacy-shadow-sweh-dogfood-2026-07-09.md; docs/aegis/hpfetcher-capsule-advisory-dogfood-2026-07-09.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260709-task233-legacy-shadow-sweh-projection-ACTIVE/`
- `aegis_foundation/legacy_projection.py`
- `aegis_foundation/cli.py`
- `.claude/scripts/ledger_lib.py`
- `scripts/_aegis_installer.py`
- `docs/aegis/`
- `.taskmaster/tasks/task_233.md`
- `tests/`
- Taskmaster Task `233`

## Branch Policy
- Working branch: `feat/task-233-legacy-shadow-sweh-projection`

## Amendments & Versioning
- 2026-07-09 - Task 233 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 233 and the projection contract.
  3. Review both downstream dogfood reports and the PR-4 parity matrix.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: add explicit MCP caller identity and wire witness/delivery boundaries before considering legacy-surface demotion.

## Conflict & Scope Declaration
- Related tasks: TM-209 capsule work, TM-229 replacement parity matrix, TM-210 PR-4 retirement.
- Guard cross-check: TM-210 depends on TM-233, but no legacy surface is authorized for retirement by this slice.

## Evidence Checklist
- Coexistence contract and PR-4 parity matrix updates
- Projection, installer, ledger, and CLI implementation tests
- HP-Fetcher and clean-install blog dogfood reports
- Tracker/session entries for implementation, verification, and Taskmaster truth

## Emergency Bypass Protocol
- No bypass authorized.
