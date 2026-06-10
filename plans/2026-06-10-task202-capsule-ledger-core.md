---
session_id: 2026-06-10-002
work_context: task202-capsule-ledger-core
handler_target: .taskmaster/tasks/task_202.txt
task_ids: [202]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/
  - .taskmaster/tasks/task_202.txt
  - .taskmaster/tasks/task_202.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 202 Capsule PR-1a: passive ledger core (store, schema, redaction)

## Header
- **Session ID (S)**: 2026-06-10-002
- **Work Context (W)**: task202-capsule-ledger-core
- **Handler Target (H)**: .taskmaster/tasks/task_202.txt
- **Task IDs**: 202
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/, .taskmaster/tasks/task_202.txt, .taskmaster/tasks/task_202.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-1a boundary from AEGIS_CAPSULE_SPEC.md sections 1.2 and 2: store path, event schema, redaction defaults, JSONL fallback contract, test matrix, and out-of-scope list; commit the spec + program-doc pointer atomically and wire the nine-PR Taskmaster backlog | docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/designs/ledger-core-scope.md | completed |
| plan-step-implement | Implement aegis_foundation/assets/.claude/scripts/ledger_lib.py (stdlib-only SQLite open/append/read, redaction helpers, backend-agnostic reader with JSONL fallback), docs/aegis/LEDGER_SCHEMA.md, and aegis ledger path + status surfacing; no hook registration | aegis_foundation/cli.py; docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Run the PR-1a test matrix (schema round-trip, concurrent writers, redaction, worktree store-path resolution, JSONL fallback parity) plus guard/plan-sync/audit stack; store evidence under reports/ and refresh handoff | docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task202-capsule-ledger-core-ACTIVE/`
- `docs/aegis/` (capsule spec, program doc pointer, LEDGER_SCHEMA.md)
- `aegis_foundation/assets/.claude/scripts/ledger_lib.py`
- `aegis_foundation/cli.py` and `scripts/_aegis_installer.py` (ledger path + status surfacing)
- `tests/claude_adapter/` and `tests/fixtures/`
- `.taskmaster/tasks/` (task 202 + nine-PR backlog wiring and reconciliation)
- Taskmaster Task `202`

## Branch Policy
- Working branch: `feat/task-202-capsule-ledger-core`

## Amendments & Versioning
- 2026-06-10 - Task 202 kickoff created via the guided wizard flow.
- 2026-06-10 - Plan rows rewritten from wizard boilerplate to the PR-1a contract (scope artifact `designs/ledger-core-scope.md`; spec sections 1.2 and 2); plan-step-scope completed.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read `docs/aegis/AEGIS_CAPSULE_SPEC.md` sections 1.2 and 2 (binding contract) and the scope artifact `designs/ledger-core-scope.md`.
  3. Review Taskmaster Task 202 and the nine-PR backlog (tasks 203+).
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: ledger_lib.py must stay stdlib-only (bootstrap fallback path); no hook registration in PR-1a; SQLite-in-hooks fragility is mitigated by the JSONL fallback contract tested against the same suite.

## Conflict & Scope Declaration
- Related plans: Aegis vNext program (`docs/aegis/AEGIS_VNEXT_PROGRAM.md`); Phase-0 backlog tasks 195-201 (reconciled by this task); HP-Coach reference deployment doc (read-only, other repo).
- Guard cross-check: PR-1a ships zero behavior change in governed repos; the assets tree gains ledger_lib.py but no settings/hook entries reference it until PR-1b.

## Evidence Checklist
- Ledger-core scope note under `designs/`
- Tracker/session entries for kickoff, contract commit, backlog wiring, and implementation progress
- Stored test and guard evidence under `reports/capsule-ledger-core/` once the implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
