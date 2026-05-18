---
session_id: 2026-05-18-002
work_context: task114-aegis-mcp-release-candidate
handler_target: .taskmaster/tasks/task_114.md
task_ids: [114]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/
  - .taskmaster/tasks/task_114.md
  - docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/designs/aegis-mcp-release-candidate-contract.md
  - tests/meta_workflow_guard/test_aegis_release_distribution.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 114 Aegis MCP Release Candidate Validation

## Header
- **Session ID (S)**: 2026-05-18-002
- **Work Context (W)**: task114-aegis-mcp-release-candidate
- **Handler Target (H)**: .taskmaster/tasks/task_114.md
- **Task IDs**: 114
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/, .taskmaster/tasks/task_114.md, docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/designs/aegis-mcp-release-candidate-contract.md, tests/meta_workflow_guard/test_aegis_release_distribution.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the Aegis MCP release-candidate contract, test matrix, release-channel decision boundary, and go/no-go criteria | docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/designs/aegis-mcp-release-candidate-contract.md | completed |
| plan-step-implement | Build and inspect release-candidate artifacts, then verify clean-project CLI and MCP install/startup workflows | tests/meta_workflow_guard/test_aegis_release_distribution.py; docs/aegis/; docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/`
- `.taskmaster/tasks/task_114.md`
- `docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/designs/aegis-mcp-release-candidate-contract.md`
- `docs/aegis/`
- `tests/meta_workflow_guard/test_aegis_release_distribution.py`
- `tests/`
- Taskmaster Task `114`

## Branch Policy
- Working branch: `feat/task-114-aegis-mcp-release-candidate`

## Amendments & Versioning
- 2026-05-18 - Task 114 kickoff created via the guided wizard flow.
- 2026-05-18 - Replaced generic wizard wording with the Aegis MCP release-candidate contract and marked `plan-step-scope` complete.
- 2026-05-18 - Completed release-candidate artifact build, clean CLI smoke, clean MCP stdio smoke, cross-agent MCP setup docs, and final verification.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 114 and its subtasks.
  3. Review the release-candidate contract before changing CLI/MCP/package behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: public publication remains a follow-up release task; Task 114 gives a go for GitHub release-candidate artifact preparation, not immediate PyPI publication.

## Conflict & Scope Declaration
- Related plans: Task 109 MCP installer foundation, Task 110 Aegis MCP installer server, Task 112 invocation contract, Task 113 release hardening.
- Guard cross-check: release-candidate validation must preserve plan/tracker/session compliance while proving installed-artifact behavior.

## Evidence Checklist
- Release-candidate contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
