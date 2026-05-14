# Task 67 Success Metrics Scope Reconciliation

## Decision

Task 67 will implement a deterministic, file-backed success metrics packet, not a live dashboard.

The historical Taskmaster wording asks for KPI widgets, trend graphs, comparative analysis views, predictive success metrics, executive summary, drill-down, and export behavior. In the current portable foundation, "dashboard" work has consistently landed as static report generation over existing evidence:

- Task 97 created `scripts/template-metrics-dashboard` for template/workflow metrics.
- Task 41 created `scripts/template-migration-health-dashboard` for aggregate migration health.
- Task 55 added `python3 scripts/codex-task migration metrics` for scanner-backed migration KPIs.
- Task 60 added `python3 scripts/codex-task migration monitoring` for post-migration monitoring packets.
- Task 68 validates the full static evidence stack.

Task 67 should extend that model by producing a top-level success metrics packet that composes existing evidence into a scorecard with JSON and Markdown outputs.

## Current Evidence

Existing repo evidence supports static aggregation:

- `reports/template-metrics/latest.json` exists and exposes Taskmaster, template metadata, drift, work-tracking, plan-sync, and wizard adoption metrics.
- `reports/template-performance/latest.json` exists as a static performance report source.
- `reports/migration-health/latest.json` is not present on current `main`, so success metrics must report that as a warning/missing upstream input with a refresh command.
- Archived work-tracking folders contain final validation, monitoring, migration metrics, knowledge transfer, and documentation evidence from completed tasks.
- `scripts/codex-task` already has static packet patterns for migration metrics, monitoring, Phase 4 documentation review, deprecation review, and knowledge transfer review.

## Proven Gap

There is no single command that answers:

"Is the foundation successful enough to keep moving, and which evidence domains block that claim?"

The current artifacts are useful but fragmented across `reports/template-metrics/`, `reports/template-performance/`, `reports/migration-health/`, final validation archive evidence, work-tracking audit, guard output, and Taskmaster health. Task 67 should add one success metrics packet that:

- calculates a transparent success score from evidence-domain statuses
- provides executive summary fields
- lists KPI/domain rows with evidence paths and refresh commands
- reports missing upstream dashboards/reports as warnings rather than fabricating data
- exports both JSON and Markdown
- remains non-destructive and portable across repo layouts

## Implementation Boundary

Implement:

- `python3 scripts/codex-task success metrics`
- JSON output with version, label, mode, action boundary, score summary, current state, KPI/domain rows, refresh commands, and non-goals
- Markdown output suitable for PR/exec review
- focused parser, builder, renderer, and handler tests
- `reports/success-metrics/README.md`

Do not implement:

- React/Vue dashboard
- live graphs or WebSocket updates
- Prometheus/Grafana integration
- database or time-series storage
- predictive analytics/ML
- automatic alerts or notifications
- external service calls
- repository mutations outside the requested report files

## Source Domains

Initial success domains should be evidence-backed and explicit:

| Domain | Primary Evidence | Expected Behavior |
| --- | --- | --- |
| Taskmaster completion | `.taskmaster/tasks/tasks.json` and `codex-task taskmaster health` semantics | Pass/warn based on done/pending counts and invalid dependencies |
| Workflow compliance | `sessions/current`, `plans/current`, active work-tracking, plan sync | Warn while work is active; pass when aligned |
| Template metrics | `reports/template-metrics/latest.json` | Pass if source exists and metadata drift is zero |
| Migration health | `reports/migration-health/latest.json` | Warn if missing; pass/warn/fail from source status when present |
| Performance evidence | `reports/template-performance/latest.json` | Pass/warn/fail from source status when present |
| Final validation | archived Task 68 final validation reports | Pass if latest final validation packet exists |
| Knowledge transfer | archived Task 54 knowledge transfer report | Pass if latest Task 54 packet exists |

## Acceptance

Task 67 is done when:

- the static success metrics packet can be generated locally
- missing upstream inputs are visible as warnings with refresh commands
- focused tests prove parser, builder, renderer, and handler behavior
- final Task 67 evidence includes the sample JSON/Markdown packet, tests, plan sync, work-tracking audit, guard, Taskmaster health, and diff-check
- Taskmaster Task 67 and subtasks are marked done after verification
