---
session_id: 2026-05-31-003
work_context: task133-codex-live-aegis-acceptance
handler_target: docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/reports/codex-live-aegis-acceptance/
task_ids: [133]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/
  - /tmp/aegis-task133-codex-live-1780220128/shop-webapp
  - .taskmaster/tasks/task_133.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 133 Run Codex Live Aegis Acceptance Test

## Header
- **Session ID (S)**: 2026-05-31-003
- **Work Context (W)**: task133-codex-live-aegis-acceptance
- **Handler Target (H)**: docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/reports/codex-live-aegis-acceptance/
- **Task IDs**: 133
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/, /tmp/aegis-task133-codex-live-1780220128/shop-webapp, .taskmaster/tasks/task_133.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Establish isolated /tmp Taskmaster-backed fixture and define Codex parity criteria | docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Run a real Codex client session with local Aegis MCP exposed and capture behavior | docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/reports/codex-live-aegis-acceptance/; /tmp/aegis-task133-codex-live-full4-R8DoDU/codex-last-message.txt | completed |
| plan-step-verify | Compare observed Codex behavior to Claude/native workflow, harden any Aegis gaps, and verify repository health | docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/TRACKER.md; cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_schemas.py tests/meta_workflow_guard/test_aegis_installer.py -q` | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260531-task133-codex-live-aegis-acceptance-ACTIVE/`
- `/tmp/aegis-task133-codex-live-1780220128/shop-webapp`
- `.taskmaster/tasks/task_133.md`
- Aegis Codex adapter/runtime hardening only if the live run exposes a repo-owned gap
- `tests/`
- Taskmaster Task `133`

## Branch Policy
- Working branch: `feat/task-133-codex-live-aegis-acceptance`

## Amendments & Versioning
- 2026-05-31 - Task 133 kickoff created via the guided wizard flow.
- 2026-05-31 - Live Codex acceptance exposed and hardened MCP-first bootstrap, Codex-default install selection, `AGENTS.md` merge behavior, Codex explicit log guidance, and duplicate task slug normalization.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 133 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: final repository guard checks and Taskmaster closeout remain.

## Conflict & Scope Declaration
- Related plans: Task 131 Taskmaster-backed Aegis acceptance, Task 132 Taskmaster MCP read-only bootstrap.
- Guard cross-check: any hardening must preserve Claude MCP behavior while bringing Codex client behavior closer to native Codex workflow expectations.

## Evidence Checklist
- Fixture baseline under `/tmp/aegis-task133-codex-live-1780220128/shop-webapp`
- Captured nested Codex stdout/stderr/events and final message
- Fixture post-run state: source diff, Aegis reports/state, Taskmaster state, project verification
- Repository hardening patches and test/guard evidence if any are required

## Emergency Bypass Protocol
- No bypass authorized.
