# Task 34 Scope Reconciliation - A/B Testing Framework

## Purpose

Task 34 asks for a LaunchDarkly-style A/B testing framework with feature flags, user segments, 10/50/100 rollout, automatic rollback, and dashboards. That wording predates the current portable foundation work and assumes a runtime product service with user traffic.

This scope gate reconciles the historical task text against the current repository so implementation stays evidence-backed and portable.

## Evidence Reviewed

- Task 40 already implemented `python3 scripts/codex-task rollout canary-plan`, a non-destructive foundation rollout planner with staged Codex/Claude/other-agent canaries, manual promotion criteria, rollback triggers, and JSON/Markdown evidence.
- Task 16 implemented the static performance harness and repo-local performance policy.
- Task 17/37/41/97 implemented static monitoring, telemetry, migration-health, and metrics report surfaces.
- Task 36 implemented a change advisory packet helper for review, impact, risk, and rollback evidence.
- This repository has no runtime service, traffic router, user identity store, notification backend, or production dashboard surface.

## Current-State Gap

The current repository has canary rollout planning, monitoring, performance, telemetry, and advisory packets. It does not have a static experiment comparison plan that answers:

- What is the control?
- What are the candidate variants?
- How should evidence be allocated and compared without routing real users?
- Which repo-local commands produce metrics for each variant?
- What stop criteria emulate the historical error-threshold/rollback intent without executing rollback?

That is the useful current-state gap for Task 34.

## Rejected Scope

The following historical items are rejected for this pass unless future evidence proves a runtime product need:

- LaunchDarkly SDK or any external feature-flag provider.
- Runtime user segmentation, traffic splitting, or feature flag assignment.
- Automatic rollback or destructive recovery execution.
- Live dashboard or notification backend.
- Persistent experiment service or database.

## Selected Implementation

Task 34 will add a non-destructive foundation experiment planner to `scripts/codex-task`:

```bash
python3 scripts/codex-task rollout experiment-plan \
  --label task34-foundation-experiment \
  --report-file docs/ai/work-tracking/active/<folder>/reports/ab-testing-framework/experiment-plan-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/ab-testing-framework/experiment-runbook-YYYY-MM-DD.md
```

The planner should:

- write deterministic JSON and optional Markdown runbook outputs
- define a control and one or more variants with static allocation percentages
- snapshot current Git/workflow/Taskmaster/Serena state using existing helper internals
- list repo-local metrics and verification commands from the existing guard, pytest, performance, monitoring, health, audit, and diff-check surfaces
- encode an error-threshold stop criterion without executing rollback
- state explicitly that no LaunchDarkly setup, traffic split, user targeting, automatic rollback, dashboard update, or notification was executed

## Acceptance Criteria

- Parser exposes `rollout experiment-plan`.
- Unit tests prove parser wiring, plan generation, Markdown rendering, and file output.
- Live evidence includes JSON and Markdown experiment plan artifacts under Task 34 reports.
- The plan is explicitly non-destructive and uses existing repo-local metrics.
- Final evidence includes focused tests, plan sync, work-tracking audit, guard validation, Taskmaster health, and diff check.

## S:W:H:E

- **2026-05-12 22:28 CEST** - [S:20260512|W:task34-ab-testing-framework|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260512-task34-ab-testing-framework-ACTIVE/designs/ab-testing-scope-reconciliation.md] Reconciled Task 34 from LaunchDarkly/runtime A-B testing to a portable, non-destructive foundation experiment planner.
