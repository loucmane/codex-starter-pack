---
session_id: 2026-06-08-003
work_context: task180-observation-artifact-collection
handler_target: scripts/_aegis_installer.py
task_ids: [180]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260608-task180-observation-artifact-collection-ACTIVE/
  - scripts/_aegis_installer.py
  - aegis_foundation/cli.py
  - tests/meta_workflow_guard/test_aegis_installer.py
  - .taskmaster/tasks/task_180.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 180 Add safe observation artifact collection to Aegis observe stop

## Header
- **Session ID (S)**: 2026-06-08-003
- **Work Context (W)**: task180-observation-artifact-collection
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 180
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260608-task180-observation-artifact-collection-ACTIVE/, scripts/_aegis_installer.py, aegis_foundation/cli.py, tests/meta_workflow_guard/test_aegis_installer.py, .taskmaster/tasks/task_180.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define safe observation artifact collection boundary | docs/ai/work-tracking/active/20260608-task180-observation-artifact-collection-ACTIVE/TRACKER.md | completed |
| plan-step-implement | Add collect-artifacts stop path without allowing arbitrary cleanup mutations | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py | completed |
| plan-step-verify | Validate artifact collection and unsafe-delta refusal paths | tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_aegis_mcp_server.py | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py` if MCP schema exposes the stop flag
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_mcp_server.py` if MCP schema changes
- Taskmaster Task `180`

## Branch Policy
- Working branch: `feat/task-180-observation-artifact-collection`

## Acceptance Criteria
- Observation mode still blocks arbitrary `rm`, source edits, Taskmaster mutations, git mutations, and unknown persistent actions.
- `aegis observe stop` refuses dirty observation state by default.
- `aegis observe stop --collect-artifacts` collects only new observation artifacts created after baseline.
- Collected artifacts move under `.aegis/reports/observations/<observation-id>/artifacts/`.
- Modified tracked files, Taskmaster files, source files, protected Aegis files, pre-existing files, symlink escapes, and unknown new files still block.
- The stop report lists collected artifacts and remaining unexpected changes.

## Amendments & Versioning
- 2026-06-08 - Task opened from HP-Coach observation dogfood after screenshots and `.playwright-mcp/` created a dirty-stop cleanup catch-22.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 180.
  3. Re-run focused observation stop tests before merge.

## Conflict & Scope Declaration
- This task does not relax observation-mode command permissions.
- This task does not make `--allow-dirty` more permissive.
- This task adds a sanctioned Aegis-owned artifact collection path only.

## Evidence Checklist
- Artifact-only observation stop collection test
- Unsafe tracked/source dirty-state refusal test
- Pre-existing artifact preservation test
- Symlink safety test
- Hook allowlist test for sanctioned stop path

## Emergency Bypass Protocol
- No bypass authorized.
