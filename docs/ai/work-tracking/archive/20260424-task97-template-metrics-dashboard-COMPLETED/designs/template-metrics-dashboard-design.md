# Task 97 Template Metrics Dashboard - Design

## Objective

Provide a repo-local metrics snapshot that shows workflow/template health without introducing a separate service. The dashboard should summarize the current state of Taskmaster progress, template metadata compliance, drift findings, work-tracking turnover, plan-sync history, and wizard kickoff adoption.

## Source Inventory

- `.taskmaster/tasks/tasks.json` - task counts, status distribution, and focus-chain progress.
- `reports/template-drift/summary-*.json` - latest drift report and category counts from Task 95.
- `.plan_state/sync.log` - plan-sync frequency and latest synced plan.
- `docs/ai/work-tracking/active/` and `docs/ai/work-tracking/archive/` - active-folder inventory and completed archive counts.
- `sessions/**/*.md` - wizard kickoff adoption signal.
- `scripts/codex-guard` helpers - governed markdown coverage and template metadata drift.

## Output Contract

- Repo-level outputs:
  - `reports/template-metrics/latest.md`
  - `reports/template-metrics/latest.json`
- Task-local evidence:
  - `docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/reports/template-metrics-dashboard/`

The repo-level files are the reusable dashboard surface. Task-local reports capture verification evidence for Task 97 itself.

## Metrics Schema

### Taskmaster
- total task count
- status counts
- focus chain state for Tasks 94-102

### Template Metadata
- governed markdown file count
- compliant file count
- drifted file count
- compliance percentage

### Drift
- latest drift report path
- generated timestamp
- total finding count
- category list

### Work Tracking
- active folder count
- active folder names
- archive folder count
- completed archive count

### Plan Sync
- entry count
- latest synced plan
- latest sync timestamp

### Wizard Adoption
- kickoff session count
- recent kickoff session paths

## Delivery Shape

- Implement as a standalone script under `scripts/` so it can run locally and in CI.
- Reuse `scripts/codex-guard` metadata helpers instead of duplicating template-governance logic.
- Keep the report static and file-based; no web server, database, or live dashboard UI in Task 97.

## Automation Plan

- Run the generator in CI after the existing guard/drift checks.
- Upload `reports/template-metrics/` as a workflow artifact.
- Document the local invocation alongside the drift-report workflow docs.

## Risks

- Wizard adoption metrics are text-derived and intentionally approximate.
- Drift metrics depend on at least one prior `drift-check` report being present.
- Taskmaster focus-chain reporting should stay explicit so portability tasks remain visible even before they start.
