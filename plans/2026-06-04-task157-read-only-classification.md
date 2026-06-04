---
session_id: 2026-06-04-001
work_context: task157-read-only-classification
handler_target: .claude/scripts/gate_lib.py aegis_foundation/assets/.claude/scripts/gate_lib.py aegis_mcp/server.py scripts/_aegis_installer.py tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py
task_ids: [157]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260604-task157-read-only-classification-ACTIVE/
  - .claude/scripts/gate_lib.py aegis_foundation/assets/.claude/scripts/gate_lib.py aegis_mcp/server.py scripts/_aegis_installer.py tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py
  - .taskmaster/tasks/task_157.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 157 Harden read-only access and tracking classification

## Header
- **Session ID (S)**: 2026-06-04-001
- **Work Context (W)**: task157-read-only-classification
- **Handler Target (H)**: `.claude/scripts/gate_lib.py`, `aegis_foundation/assets/.claude/scripts/gate_lib.py`, `aegis_mcp/server.py`, `scripts/_aegis_installer.py`, focused guard tests
- **Task IDs**: 157
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260604-task157-read-only-classification-ACTIVE/, scripts/_aegis_installer.py .claude/scripts/gate_lib.py tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py, .taskmaster/tasks/task_157.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Incorporate Claude red-team findings into Task 157 and define the guarded read-only/classification boundary | .taskmaster/tasks/task_157.md; docs/ai/work-tracking/active/20260604-task157-read-only-classification-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Confine Aegis target selection, share main/degraded read-only classification, and prevent substring-based implementation inference | .claude/scripts/gate_lib.py; aegis_foundation/assets/.claude/scripts/gate_lib.py; aegis_mcp/server.py; scripts/_aegis_installer.py; docs/ai/work-tracking/active/20260604-task157-read-only-classification-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove guard, MCP, installer, distribution, and reconcile invariants stay green | tests/claude_adapter/test_pretooluse_gates.py; tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_aegis_mcp_server.py; docs/ai/work-tracking/active/20260604-task157-read-only-classification-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260604-task157-read-only-classification-ACTIVE/`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `aegis_mcp/server.py`
- `scripts/_aegis_installer.py`
- `tests/claude_adapter/test_pretooluse_gates.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`
- `.taskmaster/tasks/task_157.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `157`

## Branch Policy
- Working branch: `feat/task-157-read-only-classification`

## Amendments & Versioning
- 2026-06-04 - Task 157 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 157 and its subtasks.
  3. Review the Task 157 implementation notes and focused test evidence before changing gate behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: close out Task 157 and open a PR after final verification/commit.

## Conflict & Scope Declaration
- Related plans: Tasks 155-156 validator and Taskmaster authority hardening; Task 158 shadow accumulation follow-on.
- Guard cross-check: read-only access must remain structural and bounded; shell parsing stays conservative.

## Evidence Checklist
- Task 157 scope update in Taskmaster
- Tracker/session entries for implementation and verification progress
- Focused guard/MCP/installer tests
- Broader distribution and reconcile safety tests

## Emergency Bypass Protocol
- No bypass authorized.
