---
session_id: 2026-05-17-004
work_context: task113-aegis-release-hardening
handler_target: .taskmaster/tasks/task_113.md
task_ids: [113]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/
  - .taskmaster/tasks/task_113.md
  - .taskmaster/tasks/task_113.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 113 Aegis Release Hardening and Distribution Readiness

## Header
- **Session ID (S)**: 2026-05-17-004
- **Work Context (W)**: task113-aegis-release-hardening
- **Handler Target (H)**: .taskmaster/tasks/task_113.md
- **Task IDs**: 113
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/, .taskmaster/tasks/task_113.md, .taskmaster/tasks/task_113.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the Task 113 release/distribution contract, scope boundary, subtask shape, and verification baseline for Aegis Release Hardening and Distribution Readiness | docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/designs/aegis-release-distribution-contract.md | completed |
| plan-step-implement | Implement package metadata, wheel-safe asset resolution, external CLI/MCP invocation, release policy docs, CI templates, and tests for Aegis Release Hardening and Distribution Readiness | docs/aegis/; pyproject.toml; aegis_foundation/; aegis_mcp/; tests/meta_workflow_guard/; docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/`
- `.taskmaster/tasks/task_113.md`
- `.taskmaster/tasks/task_113.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `113`

## Branch Policy
- Working branch: `feat/task-113-aegis-release-hardening`

## Amendments & Versioning
- 2026-05-17 - Task 113 kickoff created via the guided wizard flow.
- 2026-05-17 - Reframed the generic wizard scaffold into the Task 113 release/distribution hardening contract and marked `plan-step-scope` complete.
- 2026-05-17 - Completed Task 113 implementation and verification evidence for package metadata, wheel assets, installed CLI/MCP invocation, release policy, CI templates, release matrix, and final workflow gates.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 113 and its subtasks.
  3. Review the release/distribution contract artifact before changing package, installer, or MCP behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: archive the active work-tracking folder only after PR merge.

## Conflict & Scope Declaration
- Related plans: Tasks 109-112 Aegis installer, MCP, smoke harness, and invocation-contract work.
- Guard cross-check: release hardening must not weaken plan/tracker/session compliance or the existing Aegis installer safety model.

## Evidence Checklist
- Release/distribution contract design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence under `reports/aegis-release-hardening/`

## Emergency Bypass Protocol
- No bypass authorized.
