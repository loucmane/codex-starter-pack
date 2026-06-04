---
session_id: 2026-06-04-003
work_context: task160-shadow-evidence-hardening
handler_target: aegis_foundation/reconcile_shadow_apply.py
task_ids: [160]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/
  - aegis_foundation/reconcile_shadow_apply.py
  - .taskmaster/tasks/task_160.md
  - scripts/_aegis_installer.py
  - .github/workflows/ci.yml
plan_version: v1
emergency_bypass: false
---

# Plan - Task 160 Harden shadow accumulation evidence validation

## Header
- **Session ID (S)**: 2026-06-04-003
- **Work Context (W)**: task160-shadow-evidence-hardening
- **Handler Target (H)**: aegis_foundation/reconcile_shadow_apply.py
- **Task IDs**: 160
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/, aegis_foundation/reconcile_shadow_apply.py, .taskmaster/tasks/task_160.md, scripts/_aegis_installer.py, .github/workflows/ci.yml
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the shadow evidence hardening boundary and non-goals | docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Harden shadow authority validation, state.json semantics, invalid-context accumulation, and CI artifact policy | aegis_foundation/reconcile_shadow_apply.py; scripts/_aegis_installer.py; .github/workflows/ci.yml; docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Run targeted/full tests, store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260604-task160-shadow-evidence-hardening-ACTIVE/`
- `aegis_foundation/reconcile_shadow_apply.py`
- `.taskmaster/tasks/task_160.md`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `.github/workflows/ci.yml`
- `.gitignore`
- `tests/`
- Taskmaster Task `160`

## Branch Policy
- Working branch: `feat/task-160-shadow-evidence-hardening`

## Amendments & Versioning
- 2026-06-04 - Task 160 kickoff created via the guided wizard flow.
- 2026-06-04 - Task 160 completed: authoritative validation delegation, state.json semantic checks, invalid-context refused-only accumulation, runner-temp CI artifacts, and verification evidence captured.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 160 and its subtasks.
  3. Review the Task 160 design artifact before changing shadow evidence behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: none for Task 160. Future enablement remains out of scope.

## Conflict & Scope Declaration
- Related plans: Tasks 158-159 shadow accumulation and structural backstop work.
- Guard cross-check: shadow evidence remains measurement-only; no apply/enable path is introduced.

## Evidence Checklist
- Design note under `designs/`
- Tracker/session entries for kickoff, implementation, and verification
- Targeted and full pytest evidence captured in the tracker and handoff

## Emergency Bypass Protocol
- No bypass authorized.
