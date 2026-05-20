---
session_id: 2026-05-19-002
work_context: task116-aegis-strict-verification
handler_target: .taskmaster/tasks/task_116.md
task_ids: [116]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/
  - .taskmaster/tasks/task_116.md
  - docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/designs/strict-verification-contract.md
  - scripts/_aegis_installer.py
  - aegis_foundation/cli.py
  - aegis_mcp/server.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 116 Aegis Strict Verification and Release Certification Pipeline

## Header
- **Session ID (S)**: 2026-05-19-002
- **Work Context (W)**: task116-aegis-strict-verification
- **Handler Target (H)**: .taskmaster/tasks/task_116.md
- **Task IDs**: 116
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/, .taskmaster/tasks/task_116.md, docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/designs/strict-verification-contract.md, scripts/_aegis_installer.py, aegis_foundation/cli.py, aegis_mcp/server.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the strict verification and release certification contract against the current Aegis runtime, packaging, MCP, and installed-target surfaces | docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/designs/strict-verification-contract.md | completed |
| plan-step-implement | Implement strict verification, release certification, CLI/MCP/repo-wrapper surfaces, tests, CI, and documentation | scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py; scripts/codex-task; aegis_foundation/assets/scripts/_aegis_installer.py; aegis_foundation/assets/scripts/codex-task; tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_aegis_mcp_server.py; tests/meta_workflow_guard/test_aegis_release_distribution.py; tests/meta_workflow_guard/test_aegis_invocation_contract.py; docs/aegis/; aegis_foundation/assets/docs/aegis/; docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/reports/aegis-strict-verification/tests-2026-05-19-task116-combined.txt; docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/reports/aegis-strict-verification/tests-2026-05-19-task116-combined.txt; docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/reports/aegis-strict-verification/guard-2026-05-20-final.txt; docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/reports/aegis-strict-verification/diff-check-2026-05-20-final.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/`
- `.taskmaster/tasks/task_116.md`
- `docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE/designs/strict-verification-contract.md`
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `116`

## Branch Policy
- Working branch: `feat/task-116-aegis-strict-verification`

## Amendments & Versioning
- 2026-05-19 - Task 116 kickoff created via the guided wizard flow.
- 2026-05-19 - Replaced generic wizard-scope wording with the strict verification and release certification contract, and marked `plan-step-scope` complete.
- 2026-05-19 - Added `aegis verify --strict` to the shared installer core, CLI, Codex-task wrapper, MCP tool, packaged assets, and focused installer/MCP tests.
- 2026-05-19 - Added `aegis certify-release` and `codex-task aegis certify-release` with artifact checksum/provenance inspection, deterministic report writing, and clean installed-wheel smoke orchestration.
- 2026-05-20 - Completed release certification docs, focused regression evidence, final guard, Taskmaster health, work-tracking audit, plan sync, and diff-check closeout.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 116 and its subtasks.
  3. Review the strict verification contract before changing Aegis verifier or certification behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep strict verification and release certification grounded in shared Aegis core logic rather than creating parallel CLI-only or CI-only behavior.

## Conflict & Scope Declaration
- Related plans: Task 113 release hardening, Task 114 release-candidate validation, Task 115 installed-target workflow validation.
- Guard cross-check: strict verification and release certification must preserve plan/tracker/session compliance and installed-project portability.

## Evidence Checklist
- Strict verification contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
