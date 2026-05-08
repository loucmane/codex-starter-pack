---
session_id: 2026-05-08-005
work_context: task15-serena-integration-template-system
handler_target: .taskmaster/tasks/task_015.txt
task_ids: [15]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/
  - .taskmaster/tasks/task_015.txt
  - scripts/codex-task
  - .mcp.json
  - templates/tools/search/serena-guide.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 15 Enforce Serena Integration for Template System

## Header
- **Session ID (S)**: 2026-05-08-005
- **Work Context (W)**: task15-serena-integration-template-system
- **Handler Target (H)**: .taskmaster/tasks/task_015.txt
- **Task IDs**: 15
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/, .taskmaster/tasks/task_015.txt, scripts/codex-task, .mcp.json, templates/tools/search/serena-guide.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical mandatory-Serena wording against the current portable registry/scanner foundation and actual MCP runtime | docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/designs/serena-integration-scope-reconciliation.md | completed |
| plan-step-implement | Add Serena configuration/status enforcement and update workflow docs to describe the capability-aware Serena contract | scripts/codex-task; .mcp.json; templates/tools/search/serena-guide.md; docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/reports/serena-integration-template-system/; docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/`
- `.taskmaster/tasks/task_015.txt`
- `scripts/codex-task`
- `.mcp.json`
- `templates/tools/search/serena-guide.md`
- `templates/shared/tools/tool-selection-matrix.md`
- `templates/workflows/taskmaster/work-tracking-enforcement.md`
- `templates/workflows/memory/serena-patterns.md`
- `tests/`
- Taskmaster Task `15`

## Branch Policy
- Working branch: `feat/task-15-serena-integration-template-system`

## Amendments & Versioning
- 2026-05-08 - Task 15 kickoff created via the guided wizard flow.
- 2026-05-08 - Scope reconciled to current portable-foundation behavior: registry/scanner remain deterministic, Serena is enforced through project/Codex MCP config, memory evidence, semantic inspection, and fallback signaling.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 15 and its subtasks.
  3. Review the Serena scope reconciliation artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: none for implementation; PR review should confirm the capability-aware contract is the intended interpretation of historical Task 15 wording.

## Conflict & Scope Declaration
- Related plans: Tasks 8, 13, and 28 registry/fallback groundwork; Task 103+ Claude runtime adapter; Tasks 94-95 enforcement groundwork.
- Guard cross-check: Serena evidence must be configuration-backed and logged in tracker/session; deterministic template lookup must continue to use registry/scanner paths.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Serena status report under `reports/serena-integration-template-system/`
- Tracker/session entries for scope, implementation, Serena memory, and verification progress
- Stored pytest, guard, audit, plan-sync, and diff-check evidence under `reports/serena-integration-template-system/`

## Emergency Bypass Protocol
- No bypass authorized.
