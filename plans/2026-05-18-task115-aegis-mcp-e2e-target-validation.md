---
session_id: 2026-05-18-003
work_context: task115-aegis-mcp-e2e-target-validation
handler_target: .taskmaster/tasks/task_115.md
task_ids: [115]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/
  - .taskmaster/tasks/task_115.md
  - docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md
  - tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 115 Aegis MCP End-to-End Target Project Validation

## Header
- **Session ID (S)**: 2026-05-18-003
- **Work Context (W)**: task115-aegis-mcp-e2e-target-validation
- **Handler Target (H)**: .taskmaster/tasks/task_115.md
- **Task IDs**: 115
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/, .taskmaster/tasks/task_115.md, docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md, tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the local MCP E2E target matrix, generated fixture strategy, safety cases, and go/no-go criteria | docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md | completed |
| plan-step-implement | Implement generated target fixtures and MCP E2E tests for new, existing, partial-install, and conflict scenarios | tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/TRACKER.md | completed |
| plan-step-gap-real-projects | Add second-layer real local target-project validation for new and already-started Python, web, and backend projects | tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-real-target-projects.txt | completed |
| plan-step-gap-ready-kickoff | Prove or implement the installed-project positive path from BLOCKED to READY, including task branch, task state, sessions/current, plans/current, active work tracking, and tracker/plan alignment | docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-installed-target-runtime-matrix.txt; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-aegis-native-ready.txt; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-real-target-ready-wheel.txt; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-optional-integration-ready.txt | completed |
| plan-step-gap-workflow-scaffold | Make Aegis kickoff render a full portable workflow scaffold matching this repository's session/plan/work-tracking model instead of thin placeholder files | templates/aegis/workflow/; aegis_foundation/assets/templates/aegis/workflow/; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-19-workflow-template-scaffold.txt | completed |
| plan-step-gap-swhe-tracking | Enforce S:W:H:E tracking after installed-project mutations so successful task-scoped writes must be logged to the active session and tracker before more mutation or Stop | .claude/scripts/posttooluse-tracking.sh; .claude/scripts/tracking-stop-gate.sh; scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-19-tracking-enforcement.txt | completed |
| plan-step-gap-full-workflow-surfaces | Make installed-project `aegis log` update the same workflow surfaces this repository uses: session, tracker, implementation, changelog, handoff, and plan evidence; add a project-local Aegis CLI shim so agents can always run the command | scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py; .claude/scripts/gate_lib.py; tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py; docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-19-full-workflow-surfaces.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/`
- `.taskmaster/tasks/task_115.md`
- `docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md`
- `tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py`
- `aegis_mcp/server.py`
- `docs/aegis/`
- `templates/aegis/workflow/`
- `aegis_foundation/assets/templates/aegis/workflow/`
- `.claude/scripts/posttooluse-tracking.sh`
- `.claude/scripts/tracking-stop-gate.sh`
- `.claude/scripts/gate_lib.py`
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `tests/`
- Taskmaster Task `115`

## Branch Policy
- Working branch: `feat/task-115-aegis-mcp-e2e-target-validation`

## Amendments & Versioning
- 2026-05-18 - Task 115 kickoff created via the guided wizard flow.
- 2026-05-18 - Replaced generic wizard wording with the local MCP E2E target matrix and marked `plan-step-scope` complete.
- 2026-05-18 - Added generated MCP E2E target fixtures and tests covering happy-path, partial-install, and conflict scenarios.
- 2026-05-18 - Completed Task 115 verification and marked Taskmaster Task 115 done.
- 2026-05-18 - Reopened Task 115 before merge after PR review identified missing second-layer real target-project validation.
- 2026-05-18 - Reopened Task 115 again after manual smoke showed cold-session enforcement works but installed-project positive READY kickoff is missing.
- 2026-05-18 - Added Aegis-native kickoff and readiness fallback so installed projects can reach READY without Taskmaster or Serena.
- 2026-05-18 - Refined optional-integration semantics so stale Taskmaster does not block Aegis-native current-work unless explicitly required.
- 2026-05-18 - Added default installed-target runtime matrix coverage across copied Python/web/backend fixtures.
- 2026-05-18 - Replaced thin Aegis kickoff document bodies with packaged workflow templates that generate session, plan, tracker, findings, decisions, implementation, changelog, handoff, designs, reports, and current-work state comparable to this repository's workflow model.
- 2026-05-19 - Added portable post-mutation S:W:H:E enforcement: successful mutations create pending tracking, next mutation and Stop are blocked until `aegis log` records the work in the active session and tracker.
- 2026-05-19 - Reopened Task 115 for subtask `115.11` after live Claude testing showed `aegis log` needed to update the full workflow surface set, not only session/tracker.
- 2026-05-19 - Completed subtask `115.11`: installed-project `aegis log` now updates full workflow surfaces and the focused regression passed with `131 passed, 3 skipped`.
- 2026-05-19 - Hardened `115.11` after live retest: read-only Bash redirects to `/dev/null` no longer create pending tracking, and `aegis log` refuses non-matching evidence while pending tracking exists.
- 2026-05-19 - Fixed PR CI collection by excluding copied target-project fixtures from top-level pytest discovery; CI-equivalent local run passed with `703 passed, 3 skipped`.
- 2026-05-19 - Fixed PR CI package import behavior by installing the local project in editable mode before pytest; targeted installed-target shim regression passed with `6 passed`.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 115 and its subtasks.
  3. Review the local MCP E2E target matrix before changing tests or MCP behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: public GitHub release artifacts remain a follow-up task; Task 115 gives a local go for GitHub release-candidate artifact preparation, not immediate PyPI publication.

## Conflict & Scope Declaration
- Related plans: Task 110 Aegis MCP installer server, Task 111 cross-project install validation, Task 113 release hardening, Task 114 MCP release candidate validation.
- Guard cross-check: MCP E2E tests must prove installed/target behavior without bypassing plan/tracker/session compliance.

## Evidence Checklist
- [x] Local MCP E2E target matrix under `designs/`
- [x] Concrete copied fixture project matrix under `tests/fixtures/aegis-target-projects/`
- [x] Tracker/session entries for kickoff, implementation, verification, and final status repair
- [x] Stored MCP E2E, real target-project smoke, focused regression, wheel smoke, plan sync, Taskmaster health, audit, diff-check, and guard evidence
- [x] Aegis-native installed-project kickoff evidence proving READY without Taskmaster or Serena
- [x] Optional-integration evidence proving stale Taskmaster does not block Aegis-native READY unless explicitly required
- [x] Default installed-target runtime matrix evidence proving cold block plus positive READY path across concrete fixtures
- [x] Packaged workflow-template scaffold evidence proving Aegis kickoff creates rich workflow files, not placeholder docs
- [x] Post-mutation S:W:H:E tracking evidence proving successful task-scoped mutations require `aegis log` entries before the next mutation or Stop
- [x] Full workflow-surface accountability evidence proving `aegis log` updates implementation, changelog, handoff, and plan evidence in installed projects
- [x] CI pytest collection fix evidence proving copied target-project fixture tests are not collected by the repository's top-level pytest run
- [x] CI package install fix evidence proving installed-project local shims can import `aegis_foundation.cli` in the CI environment

## Emergency Bypass Protocol
- No bypass authorized.
