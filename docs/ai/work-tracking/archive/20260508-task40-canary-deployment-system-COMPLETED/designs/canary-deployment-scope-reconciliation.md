# Task 40 Canary Deployment Scope Reconciliation

## Purpose

Task 40 predates the current portable foundation. Its original wording asks for canary stages, health metrics, automatic promotion, rollback triggers, a status dashboard, stakeholder notifications, traffic splitting, and canary analysis reports.

This repository is a portable workflow/template foundation, not a deployable product service. The task must therefore preserve the useful rollout intent without pretending there is runtime traffic to split.

## Evidence Reviewed

- `templates/engine/core/portable-foundation-spec.md` defines a portable core plus repo-local adapter/configuration model.
- `templates/engine/validation/foundation-adoption-guide.md` already documents phased foundation adoption, optional layers, and gradual metadata-policy rollout.
- `docs/ai/work-tracking/archive/20260430-task4-scanner-configuration-system-COMPLETED/designs/backlog-alignment-audit.md` places Task 40 in the optional operational layer and requires scope reconciliation before implementation.
- `docs/ai/work-tracking/archive/20260508-task20-ci-cd-pipeline-COMPLETED/designs/ci-cd-scope-reconciliation.md` explicitly treats deployment gates as out of scope because no deployable product exists in this starter-pack repository.
- `docs/ai/work-tracking/archive/20260508-task23-migration-rehearsal-environment-COMPLETED/designs/migration-rehearsal-scope-reconciliation.md` rejects Docker/container/service orchestration where the repository has no runtime service surface.
- Current searches show no existing canary runtime, traffic splitter, service dashboard, or notification backend.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 40 Decision |
| --- | --- | --- |
| Canary stages: Codex 24h, Claude 48h, Others 72h | The repo now has Codex and Claude runtime workflow surfaces plus portable adoption guidance. A staged rollout model is useful as a planning artifact. | Encode stages as deterministic rollout-plan data. |
| Health check metrics for each stage | Existing validation is guard, pytest, taskmaster health, work-tracking audit, plan sync, diff-check, and runtime readiness. | Use these as health checks in a non-destructive plan. |
| Automatic promotion logic | There is no deployment controller or production service. | Provide promotion criteria; do not auto-promote. |
| Rollback triggers | Task 19 and guard/CI evidence provide rollback/checkpoint concepts. | Encode rollback trigger criteria in the plan. |
| Canary status dashboard | Dashboard work is optional/productization and no UI runtime exists here. | Defer dashboard. |
| Stakeholder notifications | No notification backend or stakeholder config exists in the repo. | Defer notifications. |
| Traffic splitting | No user traffic or service route exists. | Explicitly out of scope. |
| Canary analysis reports | A deterministic JSON + Markdown rollout plan is useful evidence. | Implement a planner command that writes report/runbook outputs. |

## Selected Implementation Scope

Add a non-destructive canary rollout planner to `scripts/codex-task`:

```bash
python3 scripts/codex-task rollout canary-plan \
  --label foundation-canary \
  --report-file docs/ai/work-tracking/active/<folder>/reports/canary-deployment-system/canary-plan-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/canary-deployment-system/canary-runbook-YYYY-MM-DD.md
```

The planner should:

- write deterministic JSON and optional Markdown runbook outputs
- include Codex, Claude, and other-agent stages with 24h/48h/72h minimum observation windows
- include entry criteria, health checks, promotion criteria, and rollback triggers per stage
- snapshot current Git/workflow/Taskmaster/Serena state using existing helper internals
- include recommended verification commands
- state that it executes no deployments, traffic splits, notifications, dashboard updates, promotion, or rollback actions

## Non-Goals

- No traffic splitting.
- No automatic promotion.
- No deployment dashboard.
- No notification backend.
- No service runtime.
- No Docker/container orchestration.
- No external SaaS feature flag integration.

## Acceptance Criteria

- Parser exposes `rollout canary-plan`.
- Unit tests prove parser wiring, plan generation, and Markdown rendering.
- Live evidence includes a JSON canary plan and Markdown runbook under Task 40 reports.
- The plan is explicitly non-destructive and marks service deployment features as out of scope.
- Full verification captures focused tests, full pytest, plan sync, work-tracking audit, guard, and diff-check evidence.

## Scope Result

Task 40 should be completed as a portable foundation canary rollout planner integrated into `scripts/codex-task`, not as a production deployment system. This preserves the useful staged-rollout intent while matching the current foundation architecture and avoiding fake deployment infrastructure.

## Progress Log

- **2026-05-08 18:55** — [S:20260508|W:task40-canary-deployment-system|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260508-task40-canary-deployment-system-ACTIVE/designs/canary-deployment-scope-reconciliation.md] Reconciled Task 40 against current foundation evidence and selected a non-destructive rollout planner as the current implementation gap.
