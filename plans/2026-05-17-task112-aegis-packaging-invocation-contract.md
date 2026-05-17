---
session_id: 2026-05-17-003
work_context: task112-aegis-packaging-invocation-contract
handler_target: .taskmaster/tasks/task_112.md
task_ids: [112]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/
  - .taskmaster/tasks/task_112.md
  - docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/designs/aegis-invocation-contract.md
  - pyproject.toml
  - scripts/_aegis_installer.py
  - scripts/codex-task
  - scripts/aegis-mcp-server
  - aegis_mcp/server.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 112 Aegis Packaging and Invocation Contract

## Header
- **Session ID (S)**: 2026-05-17-003
- **Work Context (W)**: task112-aegis-packaging-invocation-contract
- **Handler Target (H)**: .taskmaster/tasks/task_112.md
- **Task IDs**: 112
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/, .taskmaster/tasks/task_112.md, docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/designs/aegis-invocation-contract.md, pyproject.toml, scripts/_aegis_installer.py, scripts/codex-task, scripts/aegis-mcp-server, aegis_mcp/server.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile the external Aegis invocation options, select the V1 contract, and document non-goals before implementation | docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/designs/aegis-invocation-contract.md | completed |
| plan-step-implement | Implement the selected local-checkout, package-style, and MCP invocation surfaces with focused tests and docs | pyproject.toml; scripts/codex-task; scripts/aegis-mcp-server; aegis_mcp/server.py; tests/meta_workflow_guard/; docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store command evidence, refresh Taskmaster/work-tracking state, and hand off release/update follow-up | docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/reports/aegis-packaging-invocation-contract/; docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/`
- `.taskmaster/tasks/task_112.md`
- `docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/designs/aegis-invocation-contract.md`
- `pyproject.toml`
- `scripts/_aegis_installer.py`
- `scripts/codex-task`
- `scripts/aegis-mcp-server`
- `aegis_mcp/server.py`
- `docs/aegis/`
- `tests/`
- Taskmaster Task `112`

## Branch Policy
- Working branch: `feat/task-112-aegis-packaging-invocation-contract`

## Amendments & Versioning
- 2026-05-17 - Task 112 kickoff created via the guided wizard flow.
- 2026-05-17 - Replaced the generic wizard scaffold with the Aegis invocation-contract scope and selected V1 boundaries.
- 2026-05-17 - Completed local-checkout, editable package-style, and external MCP invocation implementation with focused pytest evidence.
- 2026-05-17 - Completed final verification evidence and marked Taskmaster Task 112 done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 112 and its subtasks.
  3. Review `designs/aegis-invocation-contract.md` before changing installer, package, or MCP behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: public wheel asset bundling, `uvx`/`pipx` release snippets, package signing, update migrations, rollback, hosted services, and CI install templates remain release-hardening follow-up work.

## Conflict & Scope Declaration
- Related plans: Tasks 109-111 Aegis installer/MCP/smoke foundation, Task 101 cross-project fixtures, Task 9 hook infrastructure follow-up.
- Guard cross-check: package and MCP invocation must preserve the existing Aegis safety contract, including dry-run planning, explicit `--apply`, and evidence reports.

## Evidence Checklist
- Invocation-contract option matrix and V1 decision under `designs/`
- External-cwd local-checkout command evidence
- Package-style invocation command evidence
- External MCP startup/configuration evidence
- Tracker/session entries for kickoff, implementation progress, and verification
- Stored test, plan-sync, audit, guard, and diff-check evidence before closeout

## Emergency Bypass Protocol
- No bypass authorized.
