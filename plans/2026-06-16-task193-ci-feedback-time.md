---
session_id: 2026-06-16-001
work_context: task193-ci-feedback-time
handler_target: .github/workflows
task_ids: [193]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/
  - .github/workflows/ci.yml
  - conftest.py
  - pyproject.toml
  - tests/meta_workflow_guard/test_guard_rules.py
  - .taskmaster/tasks/task_193.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 193 Reduce CI feedback time without reducing coverage

## Header
- **Session ID (S)**: 2026-06-16-001
- **Work Context (W)**: task193-ci-feedback-time
- **Handler Target (H)**: .github/workflows
- **Task IDs**: 193
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/, .github/workflows, .taskmaster/tasks/task_193.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Profile CI; confirm pytest dominates the only pytest job; choose pytest-xdist `-n auto --dist loadgroup` and identify parallel-safety work | docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | xdist dev dep + ci.yml `-n auto --dist loadgroup`; conftest.py per-worker git isolation; pin guard-rules to an xdist group | conftest.py; .github/workflows/ci.yml; docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Serial 1688 green + 6× `-n auto` green (323s→~60s @32c / 103s @4w); coverage preserved; evidence stored | docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/reports/task193-ci-feedback-time/tests-2026-06-16-final.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/`
- `.github/workflows/ci.yml`
- `conftest.py`
- `pyproject.toml`
- `tests/meta_workflow_guard/test_guard_rules.py`
- `.taskmaster/tasks/task_193.md`
- Taskmaster Task `193`

## Branch Policy
- Working branch: `feat/task-193-ci-feedback-time`

## Amendments & Versioning
- 2026-06-16 - Task 193 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 193 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
