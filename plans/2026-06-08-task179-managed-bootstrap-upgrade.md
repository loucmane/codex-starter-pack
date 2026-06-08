---
session_id: 2026-06-08-002
work_context: task179-managed-bootstrap-upgrade
handler_target: scripts/_aegis_installer.py
task_ids: [179]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260608-task179-managed-bootstrap-upgrade-ACTIVE/
  - scripts/_aegis_installer.py
  - tests/meta_workflow_guard/test_aegis_installer.py
  - .taskmaster/tasks/task_179.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 179 Add safe Aegis bootstrap upgrade for managed adapter files

## Header
- **Session ID (S)**: 2026-06-08-002
- **Work Context (W)**: task179-managed-bootstrap-upgrade
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 179
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260608-task179-managed-bootstrap-upgrade-ACTIVE/, scripts/_aegis_installer.py, tests/meta_workflow_guard/test_aegis_installer.py, .taskmaster/tasks/task_179.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define managed bootstrap upgrade boundary for existing Aegis installs | docs/ai/work-tracking/active/20260608-task179-managed-bootstrap-upgrade-ACTIVE/TRACKER.md | completed |
| plan-step-implement | Allow manifest-owned adapter/bootstrap files to be safely upgraded unless customized | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; tests/meta_workflow_guard/test_aegis_installer.py | completed |
| plan-step-verify | Validate HP-Coach-style dry-run and focused installer regressions | tests/meta_workflow_guard/test_aegis_installer.py; /home/loucmane/dev/hpfetcher dry-run summary | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `scripts/_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `docs/ai/work-tracking/active/20260608-task179-managed-bootstrap-upgrade-ACTIVE/`
- `.taskmaster/tasks/task_179.md`
- Taskmaster Task `179`

## Branch Policy
- Working branch: `feat/task-179-managed-bootstrap-upgrade`

## Amendments & Versioning
- 2026-06-08 - Task 179 opened after HP-Coach dry-run showed existing managed adapter/bootstrap files were classified as manual-review during dispatcher bootstrap refresh.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 179.
  3. Re-run HP-Coach `plan-install` before applying any downstream refresh.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve manual-review for genuinely customized or unknown files.

## Conflict & Scope Declaration
- Related plans: Task 178 Aegis runtime dispatch.
- Guard cross-check: this task upgrades bootstrap classification only; it does not loosen apply, closeout, or Taskmaster mutation gates.

## Evidence Checklist
- HP-Coach dry-run before/after classification
- Focused installer regression test
- Taskmaster dependency validation
- Work-tracking audit

## Emergency Bypass Protocol
- No bypass authorized.
