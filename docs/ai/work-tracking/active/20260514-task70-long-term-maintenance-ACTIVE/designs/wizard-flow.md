# Task 70 Scope Reconciliation - Long-term Maintenance

## Taskmaster Source

Task 70 asks for sustainable maintenance processes:

- maintenance schedule automation;
- health check routines;
- performance baseline updates;
- security patch process;
- dependency updates;
- maintenance metrics tracking;
- maintenance documentation;
- maintenance alerts.

That wording came from the original PRD backlog and assumes a live operations stack. The current repository has evolved into a portable, static, evidence-backed foundation. This task must therefore preserve the current system boundary: generate actionable maintenance evidence without installing schedulers, daemons, dashboards, notification systems, patch automation, or external service integrations.

## Current Evidence Reviewed

- `reports/operational-runbook/README.md` documents `python3 scripts/codex-task operations runbook`, which already composes daily, weekly, monthly, quarterly, and yearly operational procedures.
- `reports/post-migration-monitoring/README.md` documents `python3 scripts/codex-task migration monitoring`, which already turns migration metrics and migration-health reports into weekly/monthly/quarterly/yearly monitoring cadence guidance.
- `reports/template-performance/latest.json` and `reports/template-performance/latest.md` provide the current static performance evidence and baseline support.
- `reports/template-metrics/latest.json` and `reports/template-metrics/latest.md` provide current template metrics evidence.
- `scripts/template-ssot-scanner/output/data/baseline_summary.json` provides scanner baseline evidence for migration and maintenance review.
- `scripts/template-ssot-scanner/output/data/security_validation.json` plus Task 50 archive evidence provide the security validation baseline.
- Task 64 archive evidence provides a static cleanup planning packet.
- Task 65 archive evidence provides a static template quality scorecard with aggregate status `pass`, score `95.3%`, and grade `A`.
- `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task work-tracking audit`, and `python3 scripts/codex-guard validate --include-untracked` already provide current workflow health checks.

## Gap Analysis

Existing tools cover individual operational surfaces, but there is no single long-term maintenance artifact that answers:

- what maintenance evidence exists right now;
- which recurring checks are ready, warning, missing, or blocked;
- which manual maintenance actions are next;
- which commands refresh the evidence;
- which items are explicitly non-goals because they would mutate external systems or create live automation.

Task 70 should fill that aggregation gap. It should not duplicate Task 57's operational runbook or Task 60's monitoring packet. It should compose them with quality, cleanup, security, performance, Taskmaster, guard, and work-tracking evidence into one deterministic maintenance packet.

## Chosen Implementation Boundary

Implement a new static command:

```bash
python3 scripts/codex-task maintenance plan \
  --label <label> \
  --report-file <maintenance.json> \
  --runbook-file <maintenance.md>
```

The command should:

- read current local evidence files when present;
- summarize maintenance domains with pass/warn/fail/missing status;
- include exact refresh commands for each domain;
- expose manual review queues for dependency/security/update work without applying patches;
- include recurring cadence guidance by linking to existing operational runbook and post-migration monitoring helpers;
- write deterministic JSON and Markdown artifacts;
- support `--strict` so fail-level maintenance state can exit nonzero;
- support `--dry-run` so callers can inspect JSON without file writes.

## Proposed Maintenance Domains

| Domain | Purpose | Source Evidence |
| --- | --- | --- |
| workflow-health | Guard, work-tracking audit, Taskmaster health, current session/plan pointers | `scripts/codex-guard`, `scripts/codex-task taskmaster health`, `scripts/codex-task work-tracking audit` |
| operational-cadence | Daily/weekly/monthly/quarterly/yearly operating procedures | `python3 scripts/codex-task operations runbook` |
| post-migration-monitoring | Migration-health and recurring monitoring cadence | `python3 scripts/codex-task migration monitoring` and `reports/post-migration-monitoring/README.md` |
| performance-baseline | Current performance report and baseline refresh guidance | `reports/template-performance/latest.json` |
| template-quality | Current quality scorecard and improvement queue | Task 65 archive evidence and `reports/template-quality/README.md` |
| cleanup-readiness | Cleanup planning packet and non-destructive cleanup queue | Task 64 archive evidence and `reports/cleanup-automation/README.md` |
| security-maintenance | Security validation and patch-review process | `scripts/template-ssot-scanner/output/data/security_validation.json` and Task 50 archive evidence |
| dependency-maintenance | Manual dependency/update review guidance | repo manifests, Taskmaster health, security validation, and no automatic update action |

## Explicit Non-goals

- Do not install cron jobs, schedulers, daemons, background workers, or long-running maintenance services.
- Do not send Slack, email, PagerDuty, webhook, issue, PR, or ticket alerts.
- Do not apply security patches, dependency updates, formatting rewrites, cleanup actions, or remediation mutations.
- Do not create a live dashboard, time-series database, hosted monitoring service, or external integration.
- Do not mutate Taskmaster, Git, sessions, plans, scanner outputs, reports, or templates except for requested maintenance packet output files.
- Do not hide missing evidence. Missing source evidence must produce a visible warning or fail-level domain result.

## Acceptance Criteria

- `python3 scripts/codex-task maintenance plan` generates JSON and Markdown artifacts under the Task 70 reports folder.
- The packet contains domain statuses, evidence paths, refresh commands, manual action queues, and explicit non-goals.
- Tests cover parser wiring, pass/warn/fail domain summarization, missing evidence handling, Markdown rendering, handler file writes, `--dry-run`, and `--strict`.
- `reports/maintenance/README.md`, `reports/README.md`, and `templates/TOOLS.md` document the command and non-goal boundary.
- Taskmaster subtask `70.1` is marked done after this scope artifact is logged and synced.
- Taskmaster subtask `70.2` is marked done only after implementation, focused tests, generated evidence, plan sync, work-tracking audit, Taskmaster health, guard, and diff-check pass.
