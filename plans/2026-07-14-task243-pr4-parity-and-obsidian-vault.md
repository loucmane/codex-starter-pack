---
session_id: 2026-07-14-006
work_context: task243-pr4-parity-and-obsidian-vault
handler_target: aegis_foundation/obsidian_vault.py
task_ids: [243]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/
  - aegis_foundation/obsidian_vault.py
  - tests/claude_adapter/test_obsidian_vault.py
  - docs/aegis/obsidian-vault-projection.md
  - docs/aegis/pr-4-replacement-parity-matrix.md
  - .taskmaster/tasks/task_243.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 243 Refresh PR-4 Parity Evidence and Build the Derived Obsidian Vault

## Header
- **Session ID (S)**: 2026-07-14-006
- **Work Context (W)**: task243-pr4-parity-and-obsidian-vault
- **Handler Target (H)**: aegis_foundation/obsidian_vault.py
- **Task IDs**: 243
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/, aegis_foundation/obsidian_vault.py, tests/claude_adapter/test_obsidian_vault.py, docs/aegis/obsidian-vault-projection.md, docs/aegis/pr-4-replacement-parity-matrix.md, .taskmaster/tasks/task_243.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the vault authority boundary, deterministic graph model, output budgets, legacy coexistence rule, and atomic ownership contract | docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/designs/derived-obsidian-vault.md | completed |
| plan-step-implement | Implement and dogfood the read-only Obsidian projection, CLI, safety checks, tests, and public contract | aegis_foundation/obsidian_vault.py; aegis_foundation/cli.py; tests/claude_adapter/test_obsidian_vault.py; docs/aegis/obsidian-vault-projection.md | completed |
| plan-step-parity | Quantify unique legacy content and refresh every PR-4 parity row with Blog and HP-Fetcher dogfood evidence | docs/aegis/pr-4-replacement-parity-matrix.md; docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/reports/ | completed |
| plan-step-verify | Complete the read-only cross-repository audit, verification, handoff, and explicit pre-Gas-Town stopping checkpoint | docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/HANDOFF.md; docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/TRACKER.md; docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/reports/task-verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/`
- `aegis_foundation/obsidian_vault.py`
- `aegis_foundation/cli.py`
- `tests/claude_adapter/test_obsidian_vault.py`
- `docs/aegis/obsidian-vault-projection.md`
- `docs/aegis/pr-4-replacement-parity-matrix.md`
- `tests/meta_workflow_guard/test_aegis_pr4_replacement_parity_matrix.py`
- `.taskmaster/tasks/task_243.md`
- Taskmaster Task `243`

## Branch Policy
- Working branch: `feat/task-243-pr4-parity-and-obsidian-vault`

## Amendments & Versioning
- 2026-07-14 - Task 243 kickoff created via the guided wizard flow.
- 2026-07-14 - Replaced generic wizard placeholders with the reviewed vault, parity, and cross-repository audit sequence; no Gas Town migration is in scope.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 243 and its subtasks.
  3. Review `designs/derived-obsidian-vault.md` and the current parity matrix before changing projection or retirement evidence.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: prove realistic ledger-scale performance, preserve all unique legacy narrative, and make no retirement decision without row-level evidence.

## Conflict & Scope Declaration
- Related plans: Tasks 237-242 and 244-252 Aegis hardening sequence; Task 210 remains the separately gated retirement implementation.
- Guard cross-check: the vault must remain a read-only view, legacy files stay intact, and Taskmaster-to-Gas-Town migration is explicitly deferred.

## Evidence Checklist
- Vault design and public authority/safety contract
- Focused deterministic/tamper/scale tests and real-ledger dogfood evidence
- Unique-content inventory and row-complete parity matrix validation
- Final source/Blog/HP-Fetcher read-only audit and explicit stopping checkpoint

## Emergency Bypass Protocol
- No bypass authorized.
