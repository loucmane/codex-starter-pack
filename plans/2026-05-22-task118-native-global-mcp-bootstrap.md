---
session_id: 2026-05-22-002
work_context: task118-native-global-mcp-bootstrap
handler_target: aegis_foundation/cli.py
task_ids: [118]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/
  - aegis_foundation/cli.py
  - .taskmaster/tasks/task_118.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 118 Native Global MCP Bootstrap for Aegis

## Header
- **Session ID (S)**: 2026-05-22-002
- **Work Context (W)**: task118-native-global-mcp-bootstrap
- **Handler Target (H)**: aegis_foundation/cli.py
- **Task IDs**: 118
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/, aegis_foundation/cli.py, .taskmaster/tasks/task_118.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the native MCP registration contract, install-source matrix, verification expectations, and non-goals for globally installable Aegis bootstrap | docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/designs/native-mcp-bootstrap-contract.md | completed |
| plan-step-implement | Implement deterministic registration generation, optional native-client execution, verification parsing, wrapper integration, and documentation updates | aegis_foundation/cli.py; scripts/codex-task; docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused test, fresh-project, guard, audit, docs, and closeout evidence for the native global MCP bootstrap | docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/reports/native-global-mcp-bootstrap/pytest-focused-final-2026-05-22.txt; docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/reports/native-global-mcp-bootstrap/fresh-folder-native-mcp-add-2026-05-22.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/`
- `aegis_foundation/cli.py`
- `.taskmaster/tasks/task_118.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `118`

## Branch Policy
- Working branch: `feat/task-118-native-global-mcp-bootstrap`

## Amendments & Versioning
- 2026-05-22 - Task 118 kickoff created via the guided wizard flow.
- 2026-05-22 - Corrected generic wizard wording to the native global MCP bootstrap contract before implementation.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 118 and its subtasks.
  3. Review the native MCP bootstrap contract before changing registration behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep native client registration as the happy path; keep config-file writes as explicit fallback only; publish/package availability is still required before internet users can install from PyPI or a public Git ref without a local wheel artifact.

## Conflict & Scope Declaration
- Related plans: Tasks 110-117 Aegis MCP packaging, release, workflow, and closeout hardening.
- Guard cross-check: native MCP registration must preserve Aegis runtime gates and workflow scaffolding as the default project bootstrap path.

## Evidence Checklist
- [x] Native MCP bootstrap contract under `designs/`
- [x] Tracker/session entries for kickoff and implementation progress
- [x] Final focused regression matrix evidence
- [x] Fresh-folder native `claude mcp add` evidence
- [x] Generated `aegis mcp execute-registration` fresh-folder evidence
- [x] Final plan sync, work-tracking audit, guard, Taskmaster health, diff-check, and readiness evidence

## Emergency Bypass Protocol
- No bypass authorized.
