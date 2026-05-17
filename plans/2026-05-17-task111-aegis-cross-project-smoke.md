---
session_id: 2026-05-17-002
work_context: task111-aegis-cross-project-smoke
handler_target: .taskmaster/tasks/task_111.md
task_ids: [111]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/
  - .taskmaster/tasks/task_111.md
  - tests/meta_workflow_guard/test_aegis_cross_project_smoke.py
  - scripts/_aegis_installer.py
  - aegis_mcp/server.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 111 Aegis Cross-Project Install Smoke Harness and Distribution Readiness

## Header
- **Session ID (S)**: 2026-05-17-002
- **Work Context (W)**: task111-aegis-cross-project-smoke
- **Handler Target (H)**: .taskmaster/tasks/task_111.md
- **Task IDs**: 111
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/, .taskmaster/tasks/task_111.md, tests/meta_workflow_guard/test_aegis_cross_project_smoke.py, scripts/_aegis_installer.py, aegis_mcp/server.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile Task 111 against Tasks 48, 101, 109, and 110, then define the cross-project smoke matrix and safety contract | docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/designs/aegis-cross-project-smoke-matrix.md | completed |
| plan-step-implement | Add isolated temp-repo CLI and MCP smoke coverage without forking installer semantics | tests/meta_workflow_guard/test_aegis_cross_project_smoke.py; docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store test/guard/audit evidence, update Taskmaster statuses, and recommend the next distribution task | docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/`
- `.taskmaster/tasks/task_111.md`
- `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_installer_fixtures.py`
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`
- `tests/meta_workflow_guard/test_aegis_schemas.py`
- `scripts/_aegis_installer.py`
- `aegis_mcp/server.py`
- `tests/`
- Taskmaster Task `111`

## Branch Policy
- Working branch: `feat/task-111-aegis-cross-project-smoke`

## Amendments & Versioning
- 2026-05-17 - Task 111 kickoff created via the guided wizard flow.
- 2026-05-17 - Corrected generated wizard wording to the actual Aegis cross-project smoke harness scope before implementation.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 111 and its subtasks.
  3. Review the Aegis cross-project smoke matrix before changing installer or MCP behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the smoke harness grounded in `scripts/_aegis_installer.py`; the MCP wrapper must prove equivalence and must not fork installer semantics.

## Conflict & Scope Declaration
- Related plans: Task 48 portability decision, Task 101 cross-project fixtures, Task 109 Aegis installer core, Task 110 Aegis MCP wrapper.
- Guard cross-check: smoke harnesses must mutate only isolated temp target repos and tracked Task 111 evidence files.

## Evidence Checklist
- Aegis cross-project smoke matrix under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
