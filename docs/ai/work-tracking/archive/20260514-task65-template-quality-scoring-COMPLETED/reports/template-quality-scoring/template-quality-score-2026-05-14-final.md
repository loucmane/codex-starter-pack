# Template Quality Scorecard

- Label: task65
- Created at: 2026-05-14T18:19:46+02:00
- Mode: static-non-destructive-template-quality-scorecard
- Executes mutations: False
- Aggregate status: `pass`
- Quality score: 95.3%
- Quality grade: A

## Current State Snapshot

- Branch: `feat/task-65-template-quality-scoring`
- HEAD: `80b715dc2ab3a931a63f707522147c633f3360dc`
- Dirty status entries: 14
- Current session: `sessions/2026/05/2026-05-14-008-task65-template-quality-scoring.md`
- Current plan: `plans/2026-05-14-task65-template-quality-scoring.md`
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE']

## Domain Scores

| Domain | Weight | Score | Grade | Status | Target | Evidence |
| --- | ---: | ---: | --- | --- | --- | --- |
| Metadata and drift | 20 | 100.0 | `A+` | `pass` | 100% metadata coverage and 0 drift findings | `reports/template-metrics/latest.json` |
| Registry health | 15 | 82.0 | `B-` | `warn` | registry loads with unique IDs and non-empty paths | `scripts/template_registry.py` |
| Scanner complexity | 15 | 100.0 | `A+` | `pass` | 0 scanner errors, 0 scanner issues, average file size under review threshold | `scripts/template-ssot-scanner/output/data/template_scan_results.json` |
| Template performance | 15 | 100.0 | `A+` | `pass` | performance report status pass with all checks passing | `reports/template-performance/latest.json` |
| Usage analytics | 10 | 100.0 | `A+` | `pass` | latest usage analytics artifact exists with observed template references | `docs/ai/work-tracking/archive/20260513-task51-template-usage-analytics-COMPLETED/reports/template-usage-analytics/template-usage-analytics-2026-05-13.json` |
| Security audit | 10 | 80.0 | `B-` | `warn` | security audit controls available or intentionally documented | `docs/ai/work-tracking/archive/20260513-task50-security-audit-process-COMPLETED/reports/security-audit-process/security-audit-2026-05-13.json` |
| Workflow continuity | 15 | 100.0 | `A+` | `pass` | one active task with current session and plan pointers | `sessions/2026/05/2026-05-14-008-task65-template-quality-scoring.md` |

## Quality Gates

- `metadata-coverage`: `pass` - 100% metadata coverage and 0 drift findings
- `performance`: `pass` - template performance report status pass
- `scanner-complexity`: `pass` - 0 scanner errors and 0 scanner issues
- `security-review`: `warn` - security audit evidence present with non-available controls reviewed
- `workflow-continuity`: `pass` - current session, plan, and active work-tracking state aligned

## Improvement Suggestions

- `registry-health` (warning): Resolve duplicate template registry IDs.
- `usage-analytics` (info): Review zero-observed templates for documentation, lifecycle, or deprecation follow-up.
- `security-audit` (warning): Review security controls with missing evidence: phase0-security-gate.

## Recommended Refresh Commands

- `python3 scripts/codex-task report generate --kind metrics`
- `python3 scripts/codex-guard drift-check`
- `python3 scripts/template-performance-harness --strict`
- `python3 scripts/codex-task template usage-analytics --include-archive --report-file reports/template-usage-analytics/latest.json --runbook-file reports/template-usage-analytics/latest.md`
- `python3 scripts/codex-task security audit --report-file reports/security-audit-process/latest.json --runbook-file reports/security-audit-process/latest.md`
- `python3 scripts/template-ssot-scanner/scanner.py --base . --out scripts/template-ssot-scanner/output/data/template_scan_results.json --no-checkpoints --profile ci`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`

## Non-Goals

- No live dashboard, hosted UI, WebSocket, database, trend backend, scheduler, daemon, or external analytics service is created.
- No CI quality gate, pre-commit hook, policy enforcement, notification, ticket, webhook, or stakeholder message is installed or sent.
- No template, registry, metadata, Taskmaster, session, plan, work-tracking, Git, scanner, report, or external state is mutated beyond requested quality scorecard artifacts.
- No performance benchmark, scanner refresh, security audit, usage analytics scan, or drift check is executed by this scorecard command.
- No predictive quality model, machine-learning service, automatic remediation, or template rewrite suggestion engine is trained or executed.

This scorecard is static and evidence-based. It composes existing repository reports and requested output files only; it does not install dashboards, mutate templates, enforce CI gates, run benchmarks, send notifications, or contact external services.
