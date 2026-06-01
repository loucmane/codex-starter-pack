---
session_id: 2026-06-01-001
work_context: task135-isolated-mcp-registration-smoke
handler_target: docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/
task_ids: [135]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/
  - docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/
  - .taskmaster/tasks/task_135.md
  - aegis_foundation/mcp_registration.py
  - aegis_foundation/cli.py
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 135 Isolated Native MCP Registration Smoke

## Header
- **Session ID (S)**: 2026-06-01-001
- **Work Context (W)**: task135-isolated-mcp-registration-smoke
- **Handler Target (H)**: docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/
- **Task IDs**: 135
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/, docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/, .taskmaster/tasks/task_135.md, aegis_foundation/mcp_registration.py, aegis_foundation/cli.py, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the isolated native MCP registration smoke contract and safety invariants | docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Add reusable smoke helpers, package CLI command, repo wrapper command, and docs | aegis_foundation/mcp_registration.py; aegis_foundation/cli.py; scripts/codex-task; docs/aegis/ | completed |
| plan-step-verify | Exercise fake-client and real-client isolated-home smoke paths, focused tests, and guard checks | tests/meta_workflow_guard/test_aegis_native_mcp_registration.py; docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `aegis_foundation/mcp_registration.py`
- `aegis_foundation/cli.py`
- `scripts/codex-task`
- `docs/aegis/mcp-client-setup.md`
- `docs/aegis/release-verification-matrix.md`
- `tests/meta_workflow_guard/test_aegis_native_mcp_registration.py`
- `tests/meta_workflow_guard/test_aegis_release_distribution.py`
- Taskmaster Task `135`

## Branch Policy
- Working branch: `feat/task-135-isolated-mcp-registration-smoke`

## Amendments & Versioning
- 2026-06-01 - Created Task 135 after Task 134 private GitHub tag acceptance exposed the need for a repeatable isolated native client registration smoke.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 135.
  3. Keep real user config out of smoke execution; use temp homes only.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: none for Task 135; optional release certification wheel smokes remain env-gated and were not required for this task.

## Conflict & Scope Declaration
- Related work: Task 134 private GitHub distribution and cross-machine install flow.
- Guard cross-check: this task adds smoke tooling only; existing registration, execution, and verification output contracts must remain backward compatible.

## Evidence Checklist
- Fake native client registration and verification smoke tests
- Real Codex temp-home registration smoke evidence
- Real Claude temp-home registration smoke evidence
- Focused native MCP registration tests
- Release-distribution documentation parity tests

## Emergency Bypass Protocol
- No bypass authorized.
