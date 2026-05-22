---
session_id: 2026-05-20-002
work_context: task117-aegis-closeout-gate
handler_target: .taskmaster/tasks/task_117.md
task_ids: [117]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/
  - .taskmaster/tasks/task_117.md
  - .taskmaster/tasks/task_117.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 117 Aegis Closeout Gate and Live-Agent Completion Flow

## Header
- **Session ID (S)**: 2026-05-20-002
- **Work Context (W)**: task117-aegis-closeout-gate
- **Handler Target (H)**: .taskmaster/tasks/task_117.md
- **Task IDs**: 117
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/, .taskmaster/tasks/task_117.md, .taskmaster/tasks/task_117.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the portable closeout gate contract, report schema, hook boundary, handoff semantics, and installed-target test matrix | docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/designs/closeout-gate-contract.md | completed |
| plan-step-implement | Implement shared-core closeout, CLI/wrapper surfaces, hook/instruction updates, and closeout regressions | scripts/_aegis_installer.py; aegis_foundation/cli.py; scripts/codex-task; .claude/scripts/gate_lib.py; aegis_mcp/server.py; tests/ | completed |
| plan-step-verify | Store evidence, refresh handoff docs, run strict/local/CI-aligned checks, and confirm Taskmaster status | docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/reports/aegis-closeout-gate/; docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/reports/aegis-closeout-gate/live-claude-closeout-2026-05-22.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/`
- `.taskmaster/tasks/task_117.md`
- `.taskmaster/tasks/task_117.md`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `scripts/codex-task`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `docs/aegis/invocation-contract.md`
- `tests/`
- Taskmaster Task `117`

## Branch Policy
- Working branch: `feat/task-117-aegis-closeout-gate`

## Amendments & Versioning
- 2026-05-20 - Task 117 kickoff created via the guided wizard flow.
- 2026-05-20 - Replaced generic wizard wording with the Aegis closeout gate contract and marked `plan-step-scope` complete.
- 2026-05-20 - Implemented closeout core, CLI/wrapper/MCP surfaces, hook updates, generated instructions, docs, packaged assets, and regression tests; marked `plan-step-implement` complete.
- 2026-05-20 - Captured focused pytest, plan sync, work-tracking audit, guard, diff-check, readiness, and Taskmaster health evidence; marked `plan-step-verify` complete.
- 2026-05-22 - Captured fresh Claude client live closeout evidence proving installed Aegis can run the requested feature workflow through kickoff, S:W:H:E logging, strict verification, and closeout.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 117 and its subtasks.
  3. Review the closeout gate contract before changing Aegis runtime behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep closeout grounded in the shared Aegis core rather than creating a Claude-only or docs-only completion path.

## Conflict & Scope Declaration
- Related plans: Task 116 strict verification and installed-target workflow validation.
- Guard cross-check: closeout must preserve readiness, pending tracking, plan/tracker/session compliance, strict verification, and installed-project portability as the default path.

## Evidence Checklist
- Closeout gate contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test, guard, and live Claude closeout evidence

## Emergency Bypass Protocol
- No bypass authorized.
