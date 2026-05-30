---
session_id: 2026-05-29-002
work_context: task130-aegis-normal-language-workflow-acceptance
handler_target: docs/aegis/public-adoption-flow.md
task_ids: [130]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/
  - .taskmaster/tasks/task_130.md
  - docs/aegis/public-adoption-flow.md
  - docs/aegis/live-acceptance-matrix.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 130 Aegis Normal-Language Workflow Acceptance and First-Pass Closeout Hardening

## Header
- **Session ID (S)**: 2026-05-29-002
- **Work Context (W)**: task130-aegis-normal-language-workflow-acceptance
- **Handler Target (H)**: docs/aegis/public-adoption-flow.md
- **Task IDs**: 130
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/, .taskmaster/tasks/task_130.md, docs/aegis/public-adoption-flow.md, docs/aegis/live-acceptance-matrix.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the normal-language acceptance bar, target project matrix, and first-pass closeout success criteria without including public package publication | docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/DECISIONS.md; docs/aegis/public-adoption-flow.md; docs/aegis/live-acceptance-matrix.md | completed |
| plan-step-implement | Improve installed Aegis guidance, next-action responses, log defaults, handoff repair, closeout readiness, and docs only where live normal-language tests expose friction | scripts/_aegis_installer.py; aegis_foundation/assets/; aegis_mcp/server.py; docs/aegis/; docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Run fresh/existing-project live Claude acceptance with normal-language prompts, store reports, run focused regression checks, and confirm no long checklist or workflow-file hand edits are needed | docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/reports/normal-language-acceptance/; docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260529-task130-aegis-normal-language-workflow-acceptance-ACTIVE/`
- `.taskmaster/tasks/task_130.md`
- `docs/aegis/public-adoption-flow.md`
- `docs/aegis/live-acceptance-matrix.md`
- `docs/aegis/mcp-client-setup.md`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/`
- `aegis_mcp/server.py`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `130`

## Branch Policy
- Working branch: `feat/task-130-aegis-normal-language-workflow-acceptance`

## Amendments & Versioning
- 2026-05-29 - Task 130 kickoff created via the guided wizard flow.
- 2026-05-29 - Plan corrected from generic wizard wording to normal-language acceptance and first-pass closeout hardening.
- 2026-05-29 - First hardening pass aligned not-installed MCP guidance and `aegis.init` next-action output with the public `init -> start` flow.
- 2026-05-29 - Prepared the fresh temp project and minimal natural-language prompt for the first Task 130 live Claude acceptance run.
- 2026-05-30 - Final live Claude doctor retest passed; successful closeout now directs and induced Claude to run read-only `aegis.doctor` before reporting completion.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 130 and its subtasks.
  3. Review `docs/aegis/public-adoption-flow.md`, `docs/aegis/mcp-client-setup.md`, and prior Task 129 live reports before changing behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep Task 130 focused on installed workflow behavior and live normal-language acceptance; defer public package publication to a later task.

## Conflict & Scope Declaration
- Related plans: Tasks 121-129 Aegis workflow UX, release readiness, closeout repair, doctor/repair, and idempotency hardening.
- Guard cross-check: normal-language usage must still preserve plan/tracker/session compliance, pending S:W:H:E tracking, strict verification, and closeout gates.

## Evidence Checklist
- Normal-language live acceptance setup and reports
- Evidence of fresh and existing project behavior
- Tracker/session entries for acceptance findings, implementation changes, and verification progress
- Stored test and guard evidence for any behavior changes

## Emergency Bypass Protocol
- No bypass authorized.
