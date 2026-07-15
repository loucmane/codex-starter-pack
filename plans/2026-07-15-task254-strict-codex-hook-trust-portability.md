---
session_id: 2026-07-15-001
work_context: task254-strict-codex-hook-trust-portability
handler_target: .taskmaster/tasks/task_254.md
task_ids: [254]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/
  - docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/designs/hook-trust-portability-contract.md
  - docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/reports/strict-codex-hook-trust-portability/verification.md
  - .taskmaster/tasks/task_254.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 254 Complete strict Codex hook-trust portability contract

## Header
- **Session ID (S)**: 2026-07-15-001
- **Work Context (W)**: task254-strict-codex-hook-trust-portability
- **Handler Target (H)**: .taskmaster/tasks/task_254.md
- **Task IDs**: 254
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: Task 254 tracking folder, hook-trust portability contract, verification report, and generated Taskmaster task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the tracked no-bypass hook-trust contract, authority separation, fail-closed rules, and clean-worktree acceptance | docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/designs/hook-trust-portability-contract.md | completed |
| plan-step-implement | Persist and schema-validate the exact contract in live/packaged assets; make install reports supplemental; add the required regression matrix | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; schemas/aegis/foundation-manifest.schema.json; aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json; tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_codex_hook_adapter.py | completed |
| plan-step-verify | Store final evidence and pass focused/full tests, parity/static checks, Taskmaster health, plan sync, work-tracking audit, and guard validation | docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/reports/strict-codex-hook-trust-portability/verification.md; docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260715-task254-strict-codex-hook-trust-portability-COMPLETED/`
- `.taskmaster/tasks/task_254.md`
- `.taskmaster/tasks/tasks.json`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `schemas/aegis/foundation-manifest.schema.json`
- `aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_codex_hook_adapter.py`
- Taskmaster Task `254`

## Branch Policy
- Working branch: `feat/task-254-strict-hook-trust-portability`

## Amendments & Versioning
- 2026-07-15 - Task 254 kickoff created via the guided wizard flow.
- 2026-07-15 - Replaced generic kickoff wording with the reviewed Task 254 portability contract and exact implementation/test surfaces.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 254 and its subtasks.
  3. Review the hook-trust portability contract before changing verifier or installer behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: finish closeout and protected delivery without claiming client-local hook trust.

## Conflict & Scope Declaration
- Related plans: Task 253 tracked-state derivation; Task 254 persists and validates the explicit durable contract.
- Guard cross-check: clean-worktree verification must not depend on ignored installation reports.

## Evidence Checklist
- [x] Portability contract under `designs/`
- [x] Tracker/session entries for kickoff and implementation progress
- [x] Focused, repository-wide, clean-worktree, and Blog preservation evidence
- [x] Final guard/audit and source-workflow closeout evidence
- [ ] Protected CI and merge evidence

## Emergency Bypass Protocol
- No bypass authorized.
