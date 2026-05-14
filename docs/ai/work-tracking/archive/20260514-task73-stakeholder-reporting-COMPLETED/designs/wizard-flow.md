# Task 73 Stakeholder Reporting Scope Reconciliation

## Decision

Task 73 will implement a deterministic, file-backed stakeholder reporting packet, not a live executive dashboard, scheduler, notification service, or reporting platform.

The historical Taskmaster wording asks for an executive dashboard, automated report generation, cost-benefit analysis, ROI calculations, risk reporting, compliance reporting, stakeholder notifications, and report scheduling. That language predates the current portable foundation. The current repository has converged on static, evidence-backed JSON and Markdown packets that can be generated locally, committed as task evidence, and reused by humans or CI without creating external services.

## Current Evidence

Existing completed tasks provide the source material a stakeholder report should compose:

| Source | Evidence | Stakeholder Use |
| --- | --- | --- |
| Taskmaster health | `python3 scripts/codex-task taskmaster health` | Completion counts, pending work, dependency health |
| Knowledge transfer | `docs/ai/work-tracking/archive/20260514-task54-knowledge-transfer-process-COMPLETED/reports/knowledge-transfer-process/` | Documentation, onboarding, troubleshooting, handoff readiness |
| Deprecation management | `docs/ai/work-tracking/archive/20260513-task66-deprecation-management-COMPLETED/reports/deprecation-management/` | Lifecycle, migration, grace-period, archival, override readiness |
| Success metrics | `docs/ai/work-tracking/archive/20260514-task67-success-metrics-dashboard-COMPLETED/reports/success-metrics-dashboard/` | Top-level success score, warning inputs, refresh commands |
| Guard and audit evidence | archived task reports plus `python3 scripts/codex-guard validate --include-untracked` and `python3 scripts/codex-task work-tracking audit` | Process compliance and workflow state |
| Static telemetry | `reports/template-metrics/`, `reports/template-performance/`, `reports/migration-health/` | Reusable report inputs when present |

## Proven Gap

The project can now produce static review packets for operations, documentation, knowledge transfer, deprecation management, and success metrics, but there is not one stakeholder-facing packet that answers:

- What is the current executive summary?
- Which completed evidence domains are ready, warning, or missing?
- What is the task completion picture?
- What are the current risks, compliance notes, and recommended stakeholder messages?
- Which refresh commands should be run before sharing the report?
- What historical dashboard/scheduling/notification requirements remain intentionally out of scope?

## Implementation Boundary

Implement:

- `python3 scripts/codex-task stakeholder report`
- JSON output with label, mode, action boundary, current state, summary, stakeholder domains, risk/compliance notes, recommended communications, refresh commands, and non-goals
- Markdown output suitable for PR, status review, or stakeholder handoff
- focused parser, builder, renderer, and handler tests
- `reports/stakeholder-reporting/README.md`

Do not implement:

- hosted executive dashboard
- report scheduler, cron job, daemon, or background worker
- email, Slack, webhook, ticket, or notification delivery
- database, warehouse, BI tool, or analytics backend
- ROI/cost calculations that fabricate values absent from source evidence
- external service calls
- repository mutations outside the requested report files

## Proposed Source Domains

Initial stakeholder domains should be explicit and evidence-backed:

| Domain | Primary Evidence | Expected Behavior |
| --- | --- | --- |
| Taskmaster delivery health | `.taskmaster/tasks/tasks.json` | Report done/pending counts and invalid dependency status |
| Workflow compliance | `sessions/current`, `plans/current`, active work tracking, guard/audit commands | Report active/between-session state and refresh commands |
| Success metrics | Task 67 archived success metrics packet | Surface aggregate success score and warning status |
| Knowledge transfer | Task 54 archived knowledge-transfer packet | Surface readiness for onboarding and continuity |
| Deprecation governance | Task 66 archived deprecation-management packet | Surface lifecycle/compliance readiness |
| Risk and compliance summary | guard/audit/Taskmaster status plus warning/missing domains | Produce deterministic risk rows from evidence only |
| Stakeholder communication guidance | `templates/guides/communication/` and existing report summaries | Provide draft message bullets, not delivery automation |

## Acceptance

Task 73 is done when:

- the static stakeholder report packet can be generated locally
- missing upstream inputs are visible as warnings with refresh commands
- focused tests prove parser, builder, renderer, and handler behavior
- final Task 73 evidence includes the sample JSON/Markdown packet, tests, plan sync, work-tracking audit, guard, Taskmaster health, and diff-check
- Taskmaster Task 73 and subtasks are marked done after verification
