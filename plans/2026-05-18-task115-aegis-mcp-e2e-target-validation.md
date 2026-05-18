---
session_id: 2026-05-18-003
work_context: task115-aegis-mcp-e2e-target-validation
handler_target: .taskmaster/tasks/task_115.md
task_ids: [115]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/
  - .taskmaster/tasks/task_115.md
  - docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md
  - tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 115 Aegis MCP End-to-End Target Project Validation

## Header
- **Session ID (S)**: 2026-05-18-003
- **Work Context (W)**: task115-aegis-mcp-e2e-target-validation
- **Handler Target (H)**: .taskmaster/tasks/task_115.md
- **Task IDs**: 115
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/, .taskmaster/tasks/task_115.md, docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md, tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the local MCP E2E target matrix, generated fixture strategy, safety cases, and go/no-go criteria | docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md | completed |
| plan-step-implement | Implement generated target fixtures and MCP E2E tests for new, existing, partial-install, and conflict scenarios | tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/`
- `.taskmaster/tasks/task_115.md`
- `docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md`
- `tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py`
- `aegis_mcp/server.py`
- `docs/aegis/`
- `tests/`
- Taskmaster Task `115`

## Branch Policy
- Working branch: `feat/task-115-aegis-mcp-e2e-target-validation`

## Amendments & Versioning
- 2026-05-18 - Task 115 kickoff created via the guided wizard flow.
- 2026-05-18 - Replaced generic wizard wording with the local MCP E2E target matrix and marked `plan-step-scope` complete.
- 2026-05-18 - Added generated MCP E2E target fixtures and tests covering happy-path, partial-install, and conflict scenarios.
- 2026-05-18 - Completed Task 115 verification and marked Taskmaster Task 115 done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 115 and its subtasks.
  3. Review the local MCP E2E target matrix before changing tests or MCP behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: public GitHub release artifacts remain a follow-up task; Task 115 gives a local go for GitHub release-candidate artifact preparation, not immediate PyPI publication.

## Conflict & Scope Declaration
- Related plans: Task 110 Aegis MCP installer server, Task 111 cross-project install validation, Task 113 release hardening, Task 114 MCP release candidate validation.
- Guard cross-check: MCP E2E tests must prove installed/target behavior without bypassing plan/tracker/session compliance.

## Evidence Checklist
- [x] Local MCP E2E target matrix under `designs/`
- [x] Tracker/session entries for kickoff, implementation, verification, and final status repair
- [x] Stored MCP E2E, focused regression, wheel smoke, plan sync, Taskmaster health, audit, diff-check, and guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
