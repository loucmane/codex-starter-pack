---
session_id: 2026-05-31-004
work_context: task134-private-github-distribution
handler_target: docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/
task_ids: [134]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/
  - docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/
  - .taskmaster/tasks/task_134.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 134 Private GitHub Distribution and Cross-Machine Install Flow

## Header
- **Session ID (S)**: 2026-05-31-004
- **Work Context (W)**: task134-private-github-distribution
- **Handler Target (H)**: docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/
- **Task IDs**: 134
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/, docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/, .taskmaster/tasks/task_134.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the private GitHub distribution contract, command shape, and acceptance matrix for Claude/Codex across machines | docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/designs/private-github-install-flow.md | completed |
| plan-step-implement | Add first-class private GitHub registration support while preserving package, pinned, wheel, source, and public GitHub modes | aegis_foundation/mcp_registration.py; aegis_foundation/cli.py; docs/aegis/ | completed |
| plan-step-verify | Exercise command generation, fake native MCP registration, source-mode regression tests, and private-repo acceptance evidence | tests/meta_workflow_guard/test_aegis_native_mcp_registration.py; docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/ | in-progress |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/`
- `docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/`
- `.taskmaster/tasks/task_134.md`
- `aegis_foundation/mcp_registration.py`
- `aegis_foundation/cli.py`
- `docs/aegis/mcp-client-setup.md`
- `docs/aegis/distribution.md`
- `docs/aegis/invocation-contract.md`
- `tests/`
- Taskmaster Task `134`

## Branch Policy
- Working branch: `feat/task-134-private-github-distribution`

## Amendments & Versioning
- 2026-05-31 - Task 134 kickoff created via the guided wizard flow.
- 2026-05-31 - Re-scoped the generated wizard plan to the private GitHub distribution contract and acceptance path.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 134 and its subtasks.
  3. Review the private GitHub install design artifact before changing registration behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: verify the generated commands without mutating real HPFetcher; use only tmp copies for real-project acceptance.

## Conflict & Scope Declaration
- Related plans: Tasks 112-114 package invocation and release hardening, Task 123 release-candidate global MCP proof, Tasks 130-133 Claude/Codex live acceptance.
- Guard cross-check: the private GitHub path must preserve existing public package, editable checkout, wheel, source, and local MCP development flows.

## Evidence Checklist
- Private GitHub design note under `designs/private-github-install-flow.md`
- Generated Claude and Codex registration commands using private GitHub source mode
- Fresh `/tmp` install/MCP smoke evidence where feasible
- Copied real-project acceptance evidence; never mutate the real HPFetcher checkout
- Focused registration/docs tests plus final guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
