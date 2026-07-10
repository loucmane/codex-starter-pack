---
session_id: 2026-07-10-001
work_context: task235-managed-update-divergence-guard
handler_target: aegis_foundation/assets/scripts/_aegis_installer.py
task_ids: [235]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260710-task235-managed-update-divergence-guard-ACTIVE/
  - aegis_foundation/assets/scripts/_aegis_installer.py
  - scripts/codex-guard
  - tests/meta_workflow_guard/test_aegis_installer.py
  - .taskmaster/tasks/task_235.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 235 Prevent Semantic Regression in Managed Aegis Updates

## Header
- **Session ID (S)**: 2026-07-10-001
- **Work Context (W)**: task235-managed-update-divergence-guard
- **Handler Target (H)**: aegis_foundation/assets/scripts/_aegis_installer.py
- **Task IDs**: 235
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: Task 235 tracker, installer and guard sources, focused regression tests
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Reproduce the blog Task 56 regression and define managed-file baseline semantics | docs/ai/work-tracking/active/20260710-task235-managed-update-divergence-guard-ACTIVE/designs/managed-divergence-contract.md | completed |
| plan-step-implement | Restore completed-archive guard parity and add checksum/legacy-baseline divergence detection | scripts/codex-guard; aegis_foundation/assets/scripts/_aegis_installer.py | completed |
| plan-step-verify | Run focused, update-cycle, guard, schema, mirror, and authoritative test suites | docs/ai/work-tracking/active/20260710-task235-managed-update-divergence-guard-ACTIVE/reports/managed-update-divergence-guard/ | completed |
| plan-step-emergency | Optional only if a documented bypass is required | Waiver and post-mortem plan | n/a |

## Scope
- `scripts/codex-guard`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `scripts/_aegis_installer.py`
- `schemas/aegis/foundation-manifest.schema.json`
- `aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json`
- Focused installer, guard, schema, and update regression tests
- Task 235 plan, session, Taskmaster, and work-tracking evidence

## Non-Goals
- No generic managed-file extension framework beyond the checksum/baseline contract.
- No Aegis strict-mode change, PR-4 retirement, or target-repository cleanup.
- No direct mutation of the blocked blog Task 56 branch before a stable upstream merge.

## Acceptance
- Active work tracking remains preferred when exactly one ACTIVE folder exists.
- Completed current-work fallback works with an empty or absent active root.
- Completed paths outside the configured archive or without `-COMPLETED` fail closed.
- A locally diverged managed governance asset is manual-review, not safe modify.
- A pristine stale managed asset remains safely upgradeable.
- Successful installs record managed-file checksums for later updates.
- A legacy manifest can recover a prior same-path asset from its recorded source commit.
- The blog Task 56 fixture applies cleanly and a second preview is idempotent.

## Branch Policy
- Working branch: `feat/task-235-managed-update-divergence-guard`

## Continuation & Handoff
- Read the Task 56 upstream handoff before changing installer classification.
- Do not consume or modify the live blog Task 56 branch from this task.
- After upstream merge, provide an exact stable-commit retry sequence for Task 56.

## Emergency Bypass Protocol
- No bypass authorized.
