---
session_id: 2026-05-22-004
work_context: task120-fresh-local-install-proof
handler_target: .taskmaster/tasks/task_120.md
task_ids: [120]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/
  - .taskmaster/tasks/task_120.md
  - .taskmaster/tasks/task_120.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 120 Fresh-Project Local Artifact Install Proof

## Header
- **Session ID (S)**: 2026-05-22-004
- **Work Context (W)**: task120-fresh-local-install-proof
- **Handler Target (H)**: .taskmaster/tasks/task_120.md
- **Task IDs**: 120
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/, .taskmaster/tasks/task_120.md, .taskmaster/tasks/task_120.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the local-first proof boundary and no-PyPI publishing gate | docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/designs/fresh-local-install-proof.md | completed |
| plan-step-implement | Fix local-wheel portability gaps and prove fresh-target install/gates | scripts/_aegis_installer.py; aegis_foundation/assets/.claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/reports/fresh-local-install-proof/local-install-proof-summary.md | completed |
| plan-step-verify | Store local wheel, registration, fresh-target, strict verify, closeout, source-leakage, Claude live-test, and final verification evidence | docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/reports/fresh-local-install-proof/certification-report.json; docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/reports/fresh-local-install-proof/claude-live-test-result.md; docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/reports/fresh-local-install-proof/final-verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260522-task120-fresh-local-install-proof-ACTIVE/`
- `.taskmaster/tasks/task_120.md`
- `.taskmaster/tasks/task_120.md`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `.claude/scripts/codex-path-guard.sh`
- `aegis_foundation/assets/.claude/scripts/codex-path-guard.sh`
- `tests/`
- Taskmaster Task `120`

## Branch Policy
- Working branch: `feat/task-120-fresh-local-install-proof`

## Amendments & Versioning
- 2026-05-22 - Task 120 kickoff created via the guided wizard flow.
- 2026-05-22 - Plan corrected from generic wizard wording to the local fresh-project install proof actually executed.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 120 and its subtasks.
  3. Review the local install proof summary and Claude live-test prompt before publishing work.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: run the live Claude client test from `/tmp/aegis-task120-claude-live-shop-dry91w`; PyPI remains blocked until that passes.

## Conflict & Scope Declaration
- Related plans: Tasks 116-119 Aegis verification, closeout, native MCP, and local package proof.
- Guard cross-check: local artifact proof must preserve plan/tracker/session compliance and not depend on Taskmaster or Serena in the target project.

## Evidence Checklist
- Local install proof design under `designs/`
- Tracker/session entries for local artifact, fresh install, and live-test evidence
- Stored certification, registration, fresh-target, strict-verify, and closeout evidence

## Emergency Bypass Protocol
- No bypass authorized.
