---
session_id: 2026-05-31-002
work_context: task132-taskmaster-mcp-readonly-bootstrap
handler_target: .claude/scripts/gate_lib.py
task_ids: [132]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260531-task132-taskmaster-mcp-readonly-bootstrap-ACTIVE/
  - .claude/scripts/gate_lib.py
  - .taskmaster/tasks/task_132.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 132 Allow Read-Only Taskmaster MCP Discovery During Aegis Bootstrap

## Header
- **Session ID (S)**: 2026-05-31-002
- **Work Context (W)**: task132-taskmaster-mcp-readonly-bootstrap
- **Handler Target (H)**: .claude/scripts/gate_lib.py
- **Task IDs**: 132
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260531-task132-taskmaster-mcp-readonly-bootstrap-ACTIVE/, .claude/scripts/gate_lib.py, .taskmaster/tasks/task_132.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Scope the Taskmaster MCP discovery carve-out and fail-closed boundary | .taskmaster/tasks/task_132.md; docs/ai/work-tracking/active/20260531-task132-taskmaster-mcp-readonly-bootstrap-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement the explicit Taskmaster MCP read-only allowlist, asset mirror, and docs | .claude/scripts/gate_lib.py; aegis_foundation/assets/.claude/scripts/gate_lib.py; docs/aegis/mcp-client-setup.md | completed |
| plan-step-verify | Store test evidence, guard evidence, and handoff state | docs/ai/work-tracking/active/20260531-task132-taskmaster-mcp-readonly-bootstrap-ACTIVE/reports/taskmaster-mcp-readonly-bootstrap/verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260531-task132-taskmaster-mcp-readonly-bootstrap-ACTIVE/`
- `.claude/scripts/gate_lib.py`
- `.taskmaster/tasks/task_132.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `132`

## Branch Policy
- Working branch: `feat/task-132-taskmaster-mcp-readonly-bootstrap`

## Amendments & Versioning
- 2026-05-31 - Task 132 kickoff created via the guided wizard flow.
- 2026-05-31 - Retrospectively corrected generated wizard wording to the actual Task 132 scope after starting the task late.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 132 and its subtasks.
  3. Review the Taskmaster MCP discovery boundary before changing gate behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: the next hardening task should run a real Codex-session acceptance test; Task 132 only covers the Taskmaster MCP discovery gate.

## Conflict & Scope Declaration
- Related plans: Task 131 Taskmaster-backed Aegis acceptance; Task 133+ Codex adapter parity follow-up.
- Guard cross-check: the discovery carve-out must not widen mutation permissions before kickoff or after closeout.

## Evidence Checklist
- Gate implementation and packaged asset mirror
- Positive and negative pretooluse gate tests
- Stored test and guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
