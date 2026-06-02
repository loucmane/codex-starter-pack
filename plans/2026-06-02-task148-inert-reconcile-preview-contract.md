---
session_id: 2026-06-02-008
work_context: task148-inert-reconcile-preview-contract
handler_target: docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/reports/inert-reconcile-preview-contract/
task_ids: [148]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/
  - docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/reports/inert-reconcile-preview-contract/
  - .taskmaster/tasks/task_148.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 148 Add inert reconcile mutation-candidate preview contract

## Header
- **Session ID (S)**: 2026-06-02-008
- **Work Context (W)**: task148-inert-reconcile-preview-contract
- **Handler Target (H)**: docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/reports/inert-reconcile-preview-contract/
- **Task IDs**: 148
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/, docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/reports/inert-reconcile-preview-contract/, .taskmaster/tasks/task_148.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the agent-runtime safety boundary for an inert reconcile candidate preview | docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement opt-in preview output, CLI/MCP/helper exposure, docs, and guard tests | scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py; scripts/codex-task; tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/reports/inert-reconcile-preview-contract/verification-summary.md; docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/`
- `docs/ai/work-tracking/active/20260602-task148-inert-reconcile-preview-contract-ACTIVE/reports/inert-reconcile-preview-contract/`
- `.taskmaster/tasks/task_148.md`
- `scripts/codex-task`
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `docs/aegis/reconcile-mutation-candidate-preview-contract.md`
- `tests/`
- Taskmaster Task `148`

## Branch Policy
- Working branch: `feat/task-148-inert-reconcile-preview-contract`

## Amendments & Versioning
- 2026-06-02 - Task 148 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
 1. Read `sessions/current` and this plan.
 2. Review Taskmaster Task 148 and its subtasks.
  3. Review the preview contract doc before changing reconcile output shape.
 4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep candidate previews inert and report-only; do not add an apply path in this task.

## Conflict & Scope Declaration
- Related plans: Tasks 144-147 reconcile promotion, side-effect, precision,
  and rollback contracts.
- Guard cross-check: default reconcile output must remain observational and
  preview output must not become an execution API.

## Evidence Checklist
- Task 148 preview contract under `docs/aegis/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence under the active report directory

## Emergency Bypass Protocol
- No bypass authorized.
