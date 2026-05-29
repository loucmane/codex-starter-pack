---
session_id: 2026-05-28-002
work_context: task128-aegis-closeout-output-and-local-workflow
handler_target: scripts/_aegis_installer.py
task_ids: [128]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260528-task128-aegis-closeout-output-and-local-workflow-ACTIVE/
  - scripts/_aegis_installer.py
  - .claude/scripts/gate_lib.py
  - aegis_foundation/cli.py
  - aegis_mcp/server.py
  - .taskmaster/tasks/task_128.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 128 Aegis closeout output and local workflow follow-up

## Header
- **Session ID (S)**: 2026-05-28-002
- **Work Context (W)**: task128-aegis-closeout-output-and-local-workflow
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 128
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260528-task128-aegis-closeout-output-and-local-workflow-ACTIVE/, scripts/_aegis_installer.py, .claude/scripts/gate_lib.py, aegis_foundation/cli.py, aegis_mcp/server.py, .taskmaster/tasks/task_128.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Capture the live hpfetcher acceptance findings and define the Task 128 closeout/local-workflow scope | docs/ai/work-tracking/active/20260528-task128-aegis-closeout-output-and-local-workflow-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260528-task128-aegis-closeout-output-and-local-workflow-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Implement concise closeout output, local-work guidance, bootstrap gates, and unambiguous closeout state updates | scripts/_aegis_installer.py; .claude/scripts/gate_lib.py; aegis_foundation/cli.py; scripts/codex-task; aegis_mcp/server.py; docs/aegis/; aegis_foundation/assets/; tests/meta_workflow_guard/ | completed |
| plan-step-verify | Store verification evidence, rerun acceptance-style checks, and update handoff state | docs/ai/work-tracking/active/20260528-task128-aegis-closeout-output-and-local-workflow-ACTIVE/reports/task128-verification/verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- Improve normal-language Aegis local work so Claude prefers `aegis start "<title>"` over arbitrary numeric `aegis kickoff`.
- Improve `aegis closeout_ready` and `aegis closeout` terminal output so humans and agents get concise actionable summaries by default.
- Preserve full structured JSON for automation and MCP responses.
- Make passed closeout state unambiguous instead of leaving current work visually `in-progress`.

## Branch Policy
- Working branch: `feat/task-128-aegis-closeout-output-and-local-workflow`

## Amendments & Versioning
- 2026-05-28 - Task 128 started from the hpfetcher acceptance-test findings after Task 127 merge.
- 2026-05-28 - Fresh Claude acceptance found MCP `aegis.start` could be blocked before readiness; Task 128 scope expanded to make CLI/MCP start an explicit readiness bootstrap exception.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 128.
  3. Review hpfetcher acceptance findings in `FINDINGS.md`.
  4. Run focused installer/MCP tests before any live acceptance rerun.
- Outstanding risks/todos: none known after focused regression suite and live temp-project verification.

## Conflict & Scope Declaration
- Related plans: Task 121 workflow UX hardening, Task 122 workflow guidance, Task 127 handoff auto-repair.
- Guard cross-check: concise CLI output must not hide failing required gates from automation.

## Evidence Checklist
- Findings and decisions from the hpfetcher acceptance test.
- Focused pytest coverage for closeout/start behavior.
- CLI output samples for concise and JSON modes.
- Live-style acceptance evidence if behavior changes affect Claude guidance.

## Emergency Bypass Protocol
- No bypass authorized.
