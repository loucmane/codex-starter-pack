# Plan: Meta Workflow Regression Suite

**Generated**: 2025-09-29 13:35 CEST
**Session ID (S)**: 2025-09-29-002
**Work Context (W)**: task83-regression-suite
**Handler Target (H)**: scripts/codex-guard
**Task IDs**: 83
**Branch Policy**: feature-required
**Evidence Summary (E)**: sessions/2025/09/2025-09-29-002-task83-regression-suite.md; docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/TRACKER.md; reports/meta-workflow-guard/
**Plan Version**: v1
**Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                                 | Evidence                                                                                                         | Status    |
|---------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------|
| plan-step-scope     | Confirm regression suite scope with loucmane, identify assets under test   | sessions/2025/09/2025-09-29-002-task83-regression-suite.md; docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/TRACKER.md | completed |
| plan-step-implement | Add unit/integration tests, update ci wiring, update docs                  | tests/meta_workflow_guard/; scripts/codex-guard; templates/engine/enforcement/meta-workflow-guard-ci-plan.md; docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/designs/ci-integration-plan.md    | completed |
| plan-step-verify    | Run guard/tests in CI/local, store reports, update handoff                  | reports/meta-workflow-guard/; docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/TRACKER.md; sessions/2025/09/2025-09-29-002-task83-regression-suite.md | pending   |
| plan-step-emergency | Emergency bypass rationale & remediation (only if invoked)                 | Waiver note; post-mortem plan                                                                                    | not-needed |

## Scope
- scripts/codex-guard
- tests/meta_workflow_guard/** (new)
- reports/meta-workflow-guard/
- templates/engine/enforcement/meta-workflow-guard-ci-plan.md
- docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/{TRACKER.md, IMPLEMENTATION.md, FINDINGS.md, HANDOFF.md}
- sessions/2025/09/2025-09-29-002-task83-regression-suite.md
- .plan_state/sync.log

## Amendments & Versioning
- None yet. Future amendments will document timestamp, rationale, approver, and version bump.

## Continuation & Handoff
- Next owner: Codex (self) unless reassigned.
- Context reload: read current session log, tracker progress log, `.plan_state/sync.log`, previous remediation guides.
- Outstanding risks: ensure tests run in CI matrix; coordinate with timestamp gate work (Task 84).

## Conflict & Scope Declaration
- Related plans: 2025-09-27-plan-compliance-phase2 (archived), 2025-09-27-task82-meta-workflow.
- Potential conflicts: modifications to guard tests by other tasks; coordinate before merging.

## Evidence Checklist
- Guard/test outputs stored under `reports/meta-workflow-guard/`.
- Evidence bundle lives in `docs/ai/work-tracking/active/20250929-task83-regression-suite-ACTIVE/reports/meta-workflow-guard/`, capturing guard failures/passes and regression logs.
- Registration + integration suites are mandatory before plan-step-implement flips to completed.
- Pytest/coverage reports saved to `reports/meta-workflow-guard/tests/`.
- Tracker checklist mirrors plan status (including branch policy alignment).
- Serena memory summarizing regression coverage captured before closing plan.

## Emergency Bypass Protocol
- If bypass required, set Emergency Bypass to true, add `plan-step-emergency` details, schedule post-mortem within 24h.

## Completion
- All plan steps marked completed with evidence stored.
- Tracker checklist mirrors plan status.
- Serena memory + handoff updated; plan archived to `plans/archive/` when complete.
