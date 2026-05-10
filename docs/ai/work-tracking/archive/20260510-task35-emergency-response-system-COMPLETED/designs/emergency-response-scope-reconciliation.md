# Task 35 Emergency Response Scope Reconciliation

**Captured**: 2026-05-10 12:55 CEST  
**Task**: 35 - Create Emergency Response System

## Purpose

Task 35 predates the portable foundation and originally asks for an operations stack with PagerDuty, Slack webhooks, war-room procedures, emergency halt behavior, post-mortem templates, and an incident dashboard.

The current repository is a portable workflow/template foundation, not a deployed service with live users, traffic, alert routing, chat integrations, or an on-call rotation. The task must preserve the useful emergency-response intent without inventing external infrastructure.

## Evidence Reviewed

- `templates/engine/core/portable-foundation-spec.md` defines the portable foundation contract: core behavior must remain config-driven, repo-local, and reusable across project shapes.
- Task 1 codebase analysis says the foundation is strong enough for continued work but old Taskmaster backlog items must be reconciled before literal execution.
- Task 4 backlog alignment places Task 35 in the optional operational layer and requires a scope gate before implementation.
- Task 17 implemented static monitoring reports, not Prometheus/Grafana/StatsD/Elasticsearch.
- Task 18 implemented a deterministic scanner-suite security validator, not external SAST or a third-party secret-scanning service.
- Task 19 implemented non-destructive rollback checkpoint and recovery-plan helpers.
- Task 20 implemented GitHub Actions CI validation, not deployment gates.
- Task 40 implemented a non-destructive canary rollout planner, not production traffic splitting or automatic promotion.
- Task 49 implemented repository communication templates, not chat/email delivery automation.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 35 Decision |
| --- | --- | --- |
| Incident classification P0-P3 with response SLAs | Still useful as policy data for repo-local response planning. | Add a governed emergency-response policy with P0-P3 definitions and response-time targets. |
| PagerDuty integration for P0/P1 | No PagerDuty account/config exists and the repo is not a service. | Out of scope. Represent escalation guidance in generated runbooks only. |
| Slack webhooks for P2/P3 | No Slack webhook config exists and adding secrets would be inappropriate. | Out of scope. Point to Task 49 communication templates instead. |
| Emergency halt mechanism | Useful, but it must be non-destructive and evidence-driven. | Implement a planner that marks P0/P1 as halt-recommended and emits explicit stop conditions; do not auto-reset, delete, or mutate workflow state. |
| Incident response runbook | Useful and portable. | Generate Markdown runbooks from policy and current repo state. |
| War room procedures | Useful as checklist text, not an external room creation integration. | Include coordination steps in the runbook. |
| Post-mortem template | Useful as a runbook section. | Include a post-incident review template in generated Markdown. |
| Incident tracking dashboard | Dashboard productization is not proven for this repo. | Defer; use JSON + Markdown artifacts under reports for auditable tracking. |

## Selected Implementation Scope

Implement Task 35 as a repo-native emergency response planner:

```bash
python3 scripts/codex-task emergency plan \
  --severity P1 \
  --summary "Guard regression after portable foundation change" \
  --label guard-regression \
  --report-file docs/ai/work-tracking/active/<folder>/reports/emergency-response-system/emergency-plan-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/emergency-response-system/emergency-runbook-YYYY-MM-DD.md
```

The planner should:

- load severity and SLA policy from a repo-local metadata file;
- snapshot current Git, session, plan, active work-tracking, Taskmaster, and Serena state;
- classify the incident as P0-P3;
- recommend halt behavior for P0/P1 without executing halt, rollback, reset, deletion, notification, or external ticket actions;
- include response checklist steps grounded in existing helpers:
  - `python3 scripts/codex-task taskmaster health`
  - `python3 scripts/codex-task work-tracking audit`
  - `python3 scripts/codex-guard validate --include-untracked`
  - `python3 scripts/codex-task rollback checkpoint`
  - `python3 scripts/codex-task rollback plan`
  - `python3 scripts/codex-task report generate --kind all`
  - `git diff --check`
- render JSON and Markdown artifacts suitable for evidence, handoff, and post-incident review.

## Non-Goals

- No PagerDuty, Slack, email, or chat webhook integration.
- No secret-backed notification configuration.
- No production incident dashboard or web UI.
- No automatic halt state that blocks all future work.
- No automatic rollback, reset, clean, restore, branch deletion, or force push.
- No mutation of Taskmaster/session/work-tracking state beyond writing the requested emergency plan artifacts.
- No replacement for Task 17 monitoring, Task 18 security validation, Task 19 rollback, Task 20 CI, Task 40 rollout planning, or Task 49 communication templates.

## Acceptance Criteria

- `templates/metadata/emergency-response-policy.json` defines P0-P3 severity policy, halt recommendations, response checklist, escalation guidance, and post-incident review prompts.
- `python3 scripts/codex-task emergency plan` writes deterministic JSON and Markdown runbooks.
- The generated plan explicitly states that no halt, notification, rollback, dashboard update, or external incident action was executed.
- Focused tests cover parser wiring, policy loading, plan generation, runbook rendering, and file output.
- Live evidence includes a Task 35 emergency plan and runbook under the active work-tracking reports folder.
- Plan sync, work-tracking audit, guard, Taskmaster health, diff-check, and focused pytest evidence are captured before closeout.

## Scope Result

Task 35 should be completed as a portable emergency response planner integrated into `scripts/codex-task`, with repo-local policy data and non-destructive JSON/Markdown evidence. This preserves the emergency-response intent while staying inside the current foundation architecture.
