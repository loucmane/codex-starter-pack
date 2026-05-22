---
session_id: 2026-05-22-003
work_context: task119-local-package-mcp-proof
handler_target: .taskmaster/tasks/task_119.md
task_ids: [119]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/
  - .taskmaster/tasks/task_119.md
  - .taskmaster/tasks/task_119.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 119 Local-First Aegis Package and MCP Installation Proof

## Header
- **Session ID (S)**: 2026-05-22-003
- **Work Context (W)**: task119-local-package-mcp-proof
- **Handler Target (H)**: .taskmaster/tasks/task_119.md
- **Task IDs**: 119
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/, .taskmaster/tasks/task_119.md, .taskmaster/tasks/task_119.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the local-first release proof and the boundary between local artifact validation and future PyPI publication | docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/designs/local-artifact-proof.md | completed |
| plan-step-implement | Add or harden local wheel/sdist artifact proof, native MCP registration support, and documentation needed for fresh-project local installs | aegis_foundation/mcp_registration.py; scripts/_aegis_installer.py; docs/aegis/; tests/meta_workflow_guard/ | completed |
| plan-step-verify | Build local artifacts, run fresh-folder CLI/MCP workflow proof, capture evidence, and close out Task 119 gates | docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/reports/local-package-mcp-proof/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/`
- `.taskmaster/tasks/task_119.md`
- `.taskmaster/tasks/task_119.md`
- `aegis_foundation/mcp_registration.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `scripts/_aegis_installer.py`
- `scripts/codex-task`
- `docs/aegis/`
- `aegis_foundation/assets/docs/aegis/`
- `tests/`
- Taskmaster Task `119`

## Branch Policy
- Working branch: `feat/task-119-local-package-mcp-proof`

## Amendments & Versioning
- 2026-05-22 - Task 119 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 119 and its subtasks.
  3. Review `designs/local-artifact-proof.md` before changing packaging or MCP registration behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: prove the local artifact path without relying on `/home/loucmane/codex`, `AEGIS_SOURCE_ROOT`, repo-local `scripts/codex-task`, `.taskmaster/`, or `.serena/` in the target project.

## Conflict & Scope Declaration
- Related plans: Task 118 native global MCP bootstrap, Task 117 closeout gate, Task 115 MCP target validation, Task 112 packaging contract.
- Guard cross-check: local artifact proof must pass before any TestPyPI or PyPI publishing task starts.

## Evidence Checklist
- Local artifact proof design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
