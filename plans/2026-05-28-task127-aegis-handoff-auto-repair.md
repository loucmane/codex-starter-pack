---
session_id: 2026-05-28-001
work_context: task127-aegis-handoff-auto-repair
handler_target: scripts/_aegis_installer.py
task_ids: [127]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_127.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 127 Add Aegis handoff auto-repair flow

## Header
- **Session ID (S)**: 2026-05-28-001
- **Work Context (W)**: task127-aegis-handoff-auto-repair
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 127
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_127.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the handoff repair flow, prompt contract, and workflow boundary for Add Aegis handoff auto-repair flow | docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the handoff repair CLI, MCP, helper integration, and documentation for Add Aegis handoff auto-repair flow | scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py; scripts/codex-task; .claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/reports/handoff-repair-verification.md; docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260528-task127-aegis-handoff-auto-repair-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_127.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `127`

## Branch Policy
- Working branch: `feat/task-127-aegis-handoff-auto-repair`

## Amendments & Versioning
- 2026-05-28 - Task 127 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 127 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
