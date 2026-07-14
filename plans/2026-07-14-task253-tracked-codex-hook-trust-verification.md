---
session_id: 2026-07-14-006
work_context: task253-tracked-codex-hook-trust-verification
handler_target: scripts/_aegis_installer.py
task_ids: [253]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260714-task253-tracked-codex-hook-trust-verification-COMPLETED/
  - scripts/_aegis_installer.py
  - aegis_foundation/assets/scripts/_aegis_installer.py
  - tests/meta_workflow_guard/test_aegis_installer.py
  - .taskmaster/tasks/task_253.md
  - .serena/memories/2026-07-14_task253_tracked_codex_hook_trust_verification.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 253 Make Codex Hook Trust Verification Reproducible from Tracked State

## Header
- **Session ID (S)**: 2026-07-14-006
- **Work Context (W)**: task253-tracked-codex-hook-trust-verification
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 253
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260714-task253-tracked-codex-hook-trust-verification-COMPLETED/, scripts/_aegis_installer.py, aegis_foundation/assets/scripts/_aegis_installer.py, tests/meta_workflow_guard/test_aegis_installer.py, .taskmaster/tasks/task_253.md, .serena/memories/2026-07-14_task253_tracked_codex_hook_trust_verification.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the tracked hook-trust contract, clean-checkout failure model, fail-closed boundary, and rollback | docs/ai/work-tracking/archive/20260714-task253-tracked-codex-hook-trust-verification-COMPLETED/designs/tracked-hook-trust.md | completed |
| plan-step-implement | Derive strict Codex hook-trust guidance from the exact tracked manifest gate in both installer copies | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; docs/ai/work-tracking/archive/20260714-task253-tracked-codex-hook-trust-verification-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove clean-checkout success, tamper denial, source/package parity, and repository guard compliance | tests/meta_workflow_guard/test_aegis_installer.py; docs/ai/work-tracking/archive/20260714-task253-tracked-codex-hook-trust-verification-COMPLETED/reports/tracked-hook-trust/verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260714-task253-tracked-codex-hook-trust-verification-COMPLETED/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `.taskmaster/tasks/task_253.md`
- `.serena/memories/2026-07-14_task253_tracked_codex_hook_trust_verification.md`
- Taskmaster Task `253`

## Branch Policy
- Working branch: `feat/task-253-tracked-codex-hook-trust-verification`

## Amendments & Versioning
- 2026-07-14 - Task 253 kickoff created via the guided wizard flow.
- 2026-07-14 - Corrected generic wizard scaffolding to the approved three-file hook-trust remediation and evidence scope.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 253 and its subtasks.
  3. Review the tracked hook-trust design and Blog Task 70 clean-checkout reproduction before changing verifier behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve exact manifest semantics, fail closed on malformed or ambiguous gates, and retain root/packaged installer parity.

## Conflict & Scope Declaration
- Related plans: Tasks 248, 249, and 252 established first-class Codex hooks, managed migration, and stable target-local dispatch.
- Guard cross-check: ignored install reports cannot be release evidence; tracked manifest semantics must remain exact and no bypass may be introduced.

## Evidence Checklist
- Tracked hook-trust design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Clean-checkout, tamper-denial, parity, full test, and guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
