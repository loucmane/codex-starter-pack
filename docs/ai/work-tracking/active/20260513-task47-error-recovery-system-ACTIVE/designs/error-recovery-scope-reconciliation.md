# Task 47 Error Recovery Scope Reconciliation

## Context

Task 47 was created from older operational wording that asks for a full error recovery system: classification taxonomy, recovery strategies, exponential backoff, context capture, monitoring reports, user-friendly messages, recovery flowcharts, and automatic error resolution.

The current repository is a portable foundation, not a deployed application runtime. It has no live request handler, user-facing UI, job queue, monitoring backend, alert delivery service, or runtime component where automatic recovery could be executed safely.

## Evidence Reviewed

- Task 19 implemented `python3 scripts/codex-task rollback checkpoint` and `rollback plan` for non-destructive checkpoint capture and recovery guidance.
- Task 35 implemented `python3 scripts/codex-task emergency plan` with repo-local P0-P3 severity policy and non-destructive incident runbooks.
- Task 39 implemented bounded guard auto-fix and explicitly rejected broad automatic remediation.
- Task 17, Task 37, Task 41, and Task 68 provide static monitoring, telemetry, health, and final validation evidence surfaces.
- Task 34 added non-destructive experiment planning and kept automatic rollback out of scope.
- `scripts/codex-task` already exposes reusable Git, workflow, Taskmaster, and Serena snapshot helpers.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 47 Decision |
| --- | --- | --- |
| Error classification taxonomy | Still useful as policy data for repo-local planning. | Add a recovery taxonomy covering foundation error classes and severity. |
| Recovery strategies per error type | Useful if advisory, not executable. | Generate reviewed recovery steps that point to existing helpers. |
| Exponential backoff for transient errors | No runtime retry loop exists. | Model a bounded backoff schedule as guidance only. |
| Error context capture | Already feasible through Git/workflow/Taskmaster/Serena snapshots. | Include snapshots in a recovery plan manifest. |
| Error reporting to monitoring | Static monitoring reports exist, not a service backend. | Include monitoring/telemetry commands in recommended evidence. |
| User-friendly error messages | Useful as operator-facing summaries. | Render Markdown runbook summaries and stop conditions. |
| Recovery flowchart | Useful as a static decision path. | Render decision-path sections in Markdown. |
| Automatic error resolution | Unsafe in the current workflow foundation. | Out of scope; emit `executes_actions: false` and non-goals. |

## Selected Implementation Scope

Implement Task 47 as a non-destructive error recovery planner:

```bash
python3 scripts/codex-task recovery plan \
  --error-class guard \
  --summary "Guard failed after workflow date rollover" \
  --label task47-guard-recovery \
  --report-file docs/ai/work-tracking/active/<folder>/reports/error-recovery-system/recovery-plan-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/error-recovery-system/recovery-runbook-YYYY-MM-DD.md
```

The planner should:

- classify a requested error class using a repo-local taxonomy;
- include recommended severity, retryability, and escalation guidance;
- capture current Git, workflow, Taskmaster, and Serena state;
- include a bounded exponential backoff schedule for retryable classes;
- recommend existing commands for guard, audit, health, monitoring, rollback, emergency, and diff-check evidence;
- render JSON and Markdown artifacts suitable for work-tracking evidence;
- explicitly state that no retry, rollback, reset, cleanup, notification, dashboard update, or external recovery action was executed.

## Non-Goals

- No automatic retry loop.
- No automatic rollback, reset, clean, restore, branch deletion, or force push.
- No Taskmaster/session/work-tracking mutation beyond writing requested report files.
- No external monitoring, ticketing, notification, dashboard, PagerDuty, Slack, or email integration.
- No replacement for Task 19 rollback checkpoints, Task 35 emergency response plans, Task 39 guard auto-fix, or Task 68 final validation.

## Acceptance

- Parser exposes `python3 scripts/codex-task recovery plan`.
- Recovery plan JSON includes taxonomy classification, current context snapshot, backoff guidance, recommended evidence commands, and non-goals.
- Markdown runbook includes classification, decision path, backoff guidance, recovery steps, escalation guidance, and non-destructive statement.
- Focused tests cover parser wiring, unknown class rejection, plan generation, runbook rendering, and file output.
- Live evidence is stored under `reports/error-recovery-system/`.

