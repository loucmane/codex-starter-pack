# Task 65 Scope Reconciliation - Template Quality Scoring

## Current Task
- Taskmaster Task 65: Build Template Quality Scoring
- Branch: `feat/task-65-template-quality-scoring`
- Session: `sessions/2026/05/2026-05-14-008-task65-template-quality-scoring.md`
- Work tracking: `docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/`

## Historical Requirement
Task 65 was originally written as a broad quality system:

- define quality metrics for complexity, maintainability, and performance;
- implement static analysis for templates;
- calculate quality scores;
- create quality dashboards;
- add quality gates for new templates;
- generate quality improvement suggestions;
- track quality trends;
- implement quality benchmarks.

That wording predates the current portable foundation, so it is treated as historical context until current repository evidence proves the remaining gap.

## Current Evidence

| Evidence | Current State | Implication |
| --- | --- | --- |
| `reports/template-metrics/latest.json` | Captures template metadata coverage and drift summary. Current coverage is `100.0%` with `0` drift findings in the checked snapshot. | Provides quality inputs for metadata and drift, but it is not an overall quality score. |
| `reports/template-performance/latest.json` | Captures performance probes and current status. Current status is `pass` with `4/4` checks passing in the checked snapshot. | Provides performance quality input and benchmark evidence. |
| `reports/template-usage-analytics/README.md` | Documents a static template usage analytics packet over registry and workflow evidence. | Provides adoption and reference-quality inputs, but no quality score. |
| `reports/template-drift/README.md` | Documents drift outputs from `python3 scripts/codex-guard drift-check`. | Provides quality-gate evidence for metadata drift. |
| `docs/ai/work-tracking/archive/20260513-task50-security-audit-process-COMPLETED/` | Task 50 implemented a non-destructive security audit packet. | Security audit results can be composed into quality scoring without creating a new security platform. |
| `docs/ai/work-tracking/archive/20260508-task42-session-management-system-COMPLETED/` | Task 42 implemented session continuation and recovery behavior. | Workflow/session health can be included as maintainability evidence. |
| `scripts/template_registry.py` | Registry provides template discovery and metadata records. | Template quality scoring can read registry state without mutating templates. |
| `scripts/template-ssot-scanner/output/data/template_scan_results.json` | Scanner output includes file counts, line counts, categories, and keyword evidence. | Static complexity and maintainability signals can be derived from scanner output. |

## Proven Gap
There is no single reusable command that composes the current template quality evidence into a transparent quality scorecard with:

- domain scores for metadata, drift, registry, usage, performance, security, workflow/session evidence, and scanner complexity;
- weighted overall score and grade;
- quality gates and benchmark checks;
- improvement suggestions tied to missing or weak evidence;
- refresh commands for stale or missing inputs;
- explicit non-goals that prevent live dashboards, mutation, background scoring, CI policy changes, or external quality services.

## Selected Implementation Boundary
Implement a deterministic static quality scoring packet:

```bash
python3 scripts/codex-task template quality-score \
  --report-file reports/template-quality/latest.json \
  --runbook-file reports/template-quality/latest.md
```

The command should:

- read existing repository evidence only;
- calculate transparent per-domain scores and a weighted overall score;
- surface missing evidence as warning/failing domains rather than fabricating quality claims;
- render JSON and Markdown outputs;
- support `--strict` for failing when the aggregate quality status is below pass;
- support `--dry-run` for printing JSON without writing files;
- include improvement suggestions and refresh commands.

## Explicit Non-Goals
- No live dashboard, hosted UI, database, trend backend, scheduler, daemon, or external analytics system.
- No CI quality gate or pre-commit policy is installed by this task.
- No template files, registry records, metadata, Taskmaster state, session state, work-tracking state, Git state, or external service is mutated beyond requested scorecard artifacts.
- No performance benchmark is executed unless the operator runs the listed refresh command separately.
- No notifications, tickets, alerts, webhooks, stakeholder messages, or remediation tasks are created automatically.

## Acceptance
- Scope reconciliation is recorded in this design artifact.
- Taskmaster subtask `65.1` is marked done after tracker/session/plan updates.
- Implementation adds only the static quality scoring command, focused tests, report docs, and task-local evidence.
- Final verification captures pytest, plan sync, audit, Taskmaster health, guard, and diff-check evidence.
