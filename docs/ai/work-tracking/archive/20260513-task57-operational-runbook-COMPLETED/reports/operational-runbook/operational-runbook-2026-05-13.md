# Operational Runbook

- Label: task57-operational-runbook
- Created at: 2026-05-13T15:36:43+02:00
- Mode: non-destructive-operational-runbook
- Executes actions: False

## Current State Snapshot

- Branch: `feat/task-57-operational-runbook`
- HEAD: `a5b23979f6829011f995db0d2b9228a4ad88766f`
- Current session: `sessions/2026/05/2026-05-13-007-task57-operational-runbook.md`
- Current plan: `plans/2026-05-13-task57-operational-runbook.md`
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260513-task57-operational-runbook-ACTIVE']
- Taskmaster tasks: 108
- Taskmaster invalid dependency refs: 0

## Procedure Index

| Cadence | Procedure | Purpose |
| --- | --- | --- |
| daily | Daily session start | Establish current date, branch, Taskmaster, session, plan, work-tracking, and Serena evidence before implementation. |
| daily | Daily implementation logging | Keep plan, tracker, session, Taskmaster, and generated task files aligned while work is happening. |
| daily | Daily closeout and GitHub handoff | Capture evidence, commit/push with normal Git workflow when auth cache is active, and leave an unambiguous handoff. |
| weekly | Weekly static telemetry refresh | Refresh scanner, drift, metrics, monitoring, Phase 0, performance, cost, and migration-health artifacts. |
| monthly | Monthly backlog, cost, and adoption review | Review Taskmaster health, cost telemetry, active/archive work tracking, and open adoption risks before drift accumulates. |
| quarterly | Quarterly benchmark and regression review | Refresh performance baselines and compare regression evidence against current foundation expectations. |
| yearly | Yearly roadmap and planning review | Regenerate planning inputs and compare open work against the portable foundation contract. |
| as-needed | Incident, recovery, and emergency response | Classify the incident and route to emergency, recovery, rollback, advisory, or validation helpers without executing destructive actions. |
| release-or-migration-signoff | Final validation sign-off | Collect the required validation evidence bundle before merge, release, or migration sign-off. |

## Procedures

### Daily session start

- ID: `daily-start`
- Cadence: daily
- Purpose: Establish current date, branch, Taskmaster, session, plan, work-tracking, and Serena evidence before implementation.
- Owner roles: active_agent, operator_owner

Commands:
- `date '+%Y-%m-%d %H:%M:%S %Z %z'`
- `git status --short --branch`
- `task-master next`
- `task-master show <id>`
- `python3 scripts/codex-task wizard kickoff --task <id> --slug <slug>`
- `python3 scripts/codex-task sessions continue --task <id> --slug <slug>`

Evidence:
- sessions/current
- plans/current
- docs/ai/work-tracking/active/<YYYYMMDD-task-slug-ACTIVE>/TRACKER.md
- serena/memory:<session-memory-name>

### Daily implementation logging

- ID: `daily-progress`
- Cadence: daily
- Purpose: Keep plan, tracker, session, Taskmaster, and generated task files aligned while work is happening.
- Owner roles: active_agent

Commands:
- `python3 scripts/codex-task sessions update --work <work> --handler <handler> --evidence <evidence> --note <note>`
- `python3 scripts/codex-task work-tracking update --work <work> --handler <handler> --evidence <evidence> --note <note>`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task taskmaster generate-one --id <id>`

Evidence:
- current session progress log
- ACTIVE tracker/findings/decisions/implementation/handoff files
- .plan_state/plan-sync.jsonl
- .taskmaster/tasks/task_<id>.txt

### Daily closeout and GitHub handoff

- ID: `daily-closeout`
- Cadence: daily
- Purpose: Capture evidence, commit/push with normal Git workflow when auth cache is active, and leave an unambiguous handoff.
- Owner roles: active_agent, operator_owner

Commands:
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`
- `git add <paths>`
- `git commit`
- `git push`

Evidence:
- plan-sync report
- work-tracking audit report
- Taskmaster health report
- guard report
- diff-check report
- commit SHA / PR link

### Weekly static telemetry refresh

- ID: `weekly-maintenance`
- Cadence: weekly
- Purpose: Refresh scanner, drift, metrics, monitoring, Phase 0, performance, cost, and migration-health artifacts.
- Owner roles: foundation_maintainer

Commands:
- `python3 scripts/codex-task report generate --kind telemetry --strict-drift --strict-monitoring --strict-phase0 --strict-performance --strict-cost --strict-migration-health`
- `python3 scripts/codex-task migration metrics --baseline-summary <baseline_summary.json> --roadmap <roadmap.json> --security-report <security_validation.json> --report-file <metrics.json> --runbook-file <metrics.md>`
- `python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json --report-file <monitoring.json> --runbook-file <monitoring.md>`

Evidence:
- reports/template-drift/
- reports/template-metrics/
- reports/template-monitoring/
- reports/phase0-scanner-validation/
- reports/template-performance/
- reports/cost-tracking/
- reports/migration-health/
- post-migration monitoring packet

### Monthly backlog, cost, and adoption review

- ID: `monthly-review`
- Cadence: monthly
- Purpose: Review Taskmaster health, cost telemetry, active/archive work tracking, and open adoption risks before drift accumulates.
- Owner roles: operator_owner, foundation_maintainer

Commands:
- `python3 scripts/codex-task taskmaster health --report-file <taskmaster-health.txt>`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task report generate --kind cost`
- `python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json --report-file <monitoring.json> --runbook-file <monitoring.md>`

Evidence:
- Taskmaster health report
- work-tracking audit report
- cost tracking report
- post-migration monitoring packet

### Quarterly benchmark and regression review

- ID: `quarterly-review`
- Cadence: quarterly
- Purpose: Refresh performance baselines and compare regression evidence against current foundation expectations.
- Owner roles: foundation_maintainer

Commands:
- `python3 scripts/template-performance-harness --report-dir reports/template-performance`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest`
- `python3 scripts/codex-task validation final-suite --dry-run`

Evidence:
- performance report
- pytest report
- final validation dry-run

### Yearly roadmap and planning review

- ID: `yearly-planning-review`
- Cadence: yearly
- Purpose: Regenerate planning inputs and compare open work against the portable foundation contract.
- Owner roles: operator_owner, foundation_maintainer

Commands:
- `python3 scripts/template-ssot-scanner/migration_roadmap.py --data-dir scripts/template-ssot-scanner/output/data --json-out <roadmap.json> --markdown-out <roadmap.md>`
- `python3 scripts/codex-task taskmaster health --report-file <taskmaster-health.txt>`
- `python3 scripts/codex-task validation final-suite --execute --report-dir reports/final-validation-suite`

Evidence:
- migration roadmap
- Taskmaster health report
- final validation suite report and runbook

### Incident, recovery, and emergency response

- ID: `incident-response`
- Cadence: as-needed
- Purpose: Classify the incident and route to emergency, recovery, rollback, advisory, or validation helpers without executing destructive actions.
- Owner roles: active_agent, operator_owner, emergency_approver

Commands:
- `python3 scripts/codex-task recovery plan --error-class <class> --summary <summary> --report-file <recovery.json> --runbook-file <recovery.md>`
- `python3 scripts/codex-task emergency plan --severity <P0-P3> --summary <summary> --report-file <emergency.json> --runbook-file <emergency.md>`
- `python3 scripts/codex-task rollback checkpoint --label <label> --report-file <checkpoint.json>`
- `python3 scripts/codex-task rollback plan --snapshot <checkpoint.json> --report-file <rollback-plan.md>`
- `python3 scripts/codex-task change advisory --summary <summary> --review-class <class> --report-file <advisory.json> --runbook-file <advisory.md>`

Evidence:
- recovery plan/runbook
- emergency plan/runbook
- rollback checkpoint/plan
- change advisory packet
- session/tracker/decision entries

### Final validation sign-off

- ID: `validation-signoff`
- Cadence: release-or-migration-signoff
- Purpose: Collect the required validation evidence bundle before merge, release, or migration sign-off.
- Owner roles: active_agent, operator_owner, foundation_maintainer

Commands:
- `python3 scripts/codex-task validation final-suite --execute --report-dir reports/final-validation-suite`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

Evidence:
- final validation suite report
- final validation runbook
- plan sync report
- audit report
- guard report
- diff-check report

## Troubleshooting Matrix

| Symptom | First Check | Response |
| --- | --- | --- |
| Missing sessions/current or plans/current | `python3 scripts/codex-task work-tracking audit` | Use wizard kickoff for a new task or sessions continue for the next day on an already-active task. |
| Filtered Taskmaster list shows dependency warnings | `python3 scripts/codex-task taskmaster health` | Treat full-graph health as authoritative before running dependency repair commands. |
| Guard validation fails | `python3 scripts/codex-guard validate --include-untracked` | Capture a recovery plan for guard failures and repair the named lifecycle or evidence gap. |
| GitHub fetch, push, merge, or signed commit fails with auth/signing errors | `git status --short --branch` | Refresh the local SSH/GPG cache, then retry the same operation without disabling signing or verification. |
| ACTIVE work-tracking folder appears stale | `python3 scripts/codex-task work-tracking audit` | Continue the active task with sessions continue; archive only after the task PR is merged. |
| Monitoring, metrics, or migration-health status is warn/fail | `python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json` | Use the required-actions list in the generated monitoring packet before closing the review. |

## Role-Based Escalation

| Level | Role | Trigger | Action |
| --- | --- | --- | --- |
| 1 | `active_agent` | Routine task execution, validation, and evidence updates. | Record S:W:H:E evidence in session, tracker, and task-local reports. |
| 2 | `operator_owner` | Ambiguous scope, auth/cache refresh, merge decision, protected-path change, or destructive command request. | Give explicit instruction and ensure decisions are logged before mutation. |
| 3 | `foundation_maintainer` | Portable foundation contract, guard, Taskmaster graph, template policy, or cross-project behavior needs review. | Require change advisory, focused tests, guard evidence, and handoff notes. |
| 4 | `emergency_approver` | P0/P1 emergency, security boundary issue, protected-surface incident, or bypass request. | Require emergency plan/runbook, rollback checkpoint, explicit approval, and post-incident follow-up. |

## Validation Checklist

| Check | Command | Evidence |
| --- | --- | --- |
| `date-confirmed` | `date '+%Y-%m-%d %H:%M:%S %Z %z'` | session validation entry |
| `branch-task-aligned` | `git status --short --branch` | branch/status report |
| `taskmaster-health` | `python3 scripts/codex-task taskmaster health` | Taskmaster health report |
| `plan-sync` | `python3 scripts/codex-task plan sync` | plan sync report/log entry |
| `work-tracking-audit` | `python3 scripts/codex-task work-tracking audit` | work-tracking audit report |
| `guard-validation` | `python3 scripts/codex-guard validate --include-untracked` | guard report |
| `focused-tests` | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <focused tests>` | pytest report |
| `diff-check` | `git diff --check` | diff-check report |
| `final-validation` | `python3 scripts/codex-task validation final-suite --execute --report-dir reports/final-validation-suite` | final suite JSON and Markdown runbook |
| `handoff-current` | `Review HANDOFF.md and Serena memory references` | handoff and memory references |

## Related Helpers

- change_advisory: `python3 scripts/codex-task change advisory --summary <summary>`
- daily_continuation: `python3 scripts/codex-task sessions continue --task <id> --slug <slug>`
- daily_start: `python3 scripts/codex-task wizard kickoff --task <id> --slug <slug>`
- emergency_plan: `python3 scripts/codex-task emergency plan --severity <P0-P3> --summary <summary>`
- final_validation: `python3 scripts/codex-task validation final-suite --execute --report-dir reports/final-validation-suite`
- guard: `python3 scripts/codex-guard validate --include-untracked`
- post_migration_monitoring: `python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json`
- recovery_plan: `python3 scripts/codex-task recovery plan --error-class <class> --summary <summary>`
- taskmaster_health: `python3 scripts/codex-task taskmaster health`
- work_tracking_audit: `python3 scripts/codex-task work-tracking audit`

## Non-Goals

- No scheduler, daemon, cron job, or background worker is installed.
- No live dashboard, hosted observability service, database, or production endpoint is contacted.
- No Slack, email, PagerDuty, ticket, issue, webhook, or contact-directory action is sent or updated.
- No deployment, promotion, traffic split, rollback, reset, clean, restore, branch deletion, or force push is executed.
- No Taskmaster, session, plan, or work-tracking state is mutated beyond the requested runbook artifacts.
- No external incident, approval, meeting, or on-call system is created.

No scheduler, notification, ticket, dashboard update, deployment, rollback, reset, cleanup, or external incident action was executed by this runbook.
