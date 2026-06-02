---
session_id: 2026-06-02-001
work_context: task141-reconcile-report
handler_target: scripts/_aegis_installer.py
task_ids: [141]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260602-task141-reconcile-report-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_141.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 141 Add read-only Aegis reconciliation report

## Header
- **Session ID (S)**: 2026-06-02-001
- **Work Context (W)**: task141-reconcile-report
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 141
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260602-task141-reconcile-report-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_141.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define read-only reconciliation report semantics, drift classes, and squash-merge ambiguity handling | tests/meta_workflow_guard/test_aegis_installer.py | completed |
| plan-step-implement | Implement reconcile core, package CLI, repo wrapper, MCP tool, and read-only gate classification | scripts/_aegis_installer.py; aegis_foundation/cli.py; scripts/codex-task; aegis_mcp/server.py; .claude/scripts/gate_lib.py | completed |
| plan-step-verify | Verify focused/full test suites, Taskmaster health, asset parity, and live reconcile smoke output | tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_aegis_mcp_server.py; tests/claude_adapter/test_pretooluse_gates.py; docs/ai/work-tracking/active/20260602-task141-reconcile-report-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260602-task141-reconcile-report-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `.claude/scripts/gate_lib.py`
- `.taskmaster/tasks/task_141.md`
- `scripts/codex-task`
- `aegis_foundation/assets/`
- `tests/`
- Taskmaster Task `141`

## Branch Policy
- Working branch: `feat/task-141-reconcile-report`

## Amendments & Versioning
- 2026-06-02 - Task 141 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 141 and its subtasks.
  3. Review the reconcile drift classes and squash ambiguity behavior before changing report semantics.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: future auto-reconciliation must not mutate status until this report proves low-noise behavior across real project history.

## Conflict & Scope Declaration
- Related plans: Tasks 137-140 agent-runtime gate hardening and degraded-event observability.
- Guard cross-check: reconcile must remain read-only and must not become a status mutation path.

## Evidence Checklist
- Focused reconcile/CLI/MCP/gate tests passed.
- Full pytest suite passed.
- Taskmaster health passed with Task 141 done.
- Live no-GitHub reconcile smoke returned CLEAN with 0 findings.
- Live GitHub-enabled reconcile smoke returned only historical multi-PR ambiguity warnings.

## Emergency Bypass Protocol
- No bypass authorized.
