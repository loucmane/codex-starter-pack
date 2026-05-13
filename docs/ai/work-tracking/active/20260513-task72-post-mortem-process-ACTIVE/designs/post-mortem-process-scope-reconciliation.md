# Task 72 Post-Mortem Process Scope Reconciliation

**Captured**: 2026-05-13 17:20 CEST  
**Task**: 72 - Implement Post-Mortem Process  
**Branch**: `feat/task-72-post-mortem-process`

## Historical Task Wording

Task 72 asks for a systematic post-mortem process for incidents:

- post-mortem template;
- incident timeline reconstruction;
- root cause analysis tools;
- action item tracking;
- follow-up automation;
- post-mortem metrics;
- knowledge extraction;
- prevention measures tracking.

That wording predates the current portable foundation. The repository is now a static, file-backed workflow foundation with deterministic helpers, local/CI guard gates, Taskmaster state, session/plan/work-tracking evidence, and JSON/Markdown reports. It is not a live incident management system, ticketing system, knowledge base, dashboard, notification service, or follow-up automation daemon.

## Evidence Reviewed

- Task 35 implemented `python3 scripts/codex-task emergency plan`, a non-destructive emergency response planner with post-incident review prompts.
- Task 47 implemented `python3 scripts/codex-task recovery plan`, a non-destructive recovery classification and remediation planner.
- Task 19 implemented rollback checkpoint and rollback-plan helpers without destructive restore execution.
- Task 44 implemented `python3 scripts/codex-task change advisory`, a non-destructive change review packet.
- Task 57 implemented `python3 scripts/codex-task operations runbook`, a static operational runbook composer with incident routing, troubleshooting, escalation, and validation guidance.
- Task 56 implemented `python3 scripts/codex-task automation phase3-review`, a static automation integration review packet over existing evidence.
- `reports/README.md` and `templates/TOOLS.md` now describe static Markdown/JSON reporting rather than hosted dashboards, external observability, tickets, notifications, or long-running services.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 72 Decision |
| --- | --- | --- |
| Create post-mortem template | Emergency response already includes review prompts, but there is no dedicated post-mortem packet. | Create a deterministic Markdown/JSON post-mortem packet with fixed sections. |
| Incident timeline reconstruction | No live event store exists. Session logs, report paths, and manual timeline entries are the durable evidence. | Accept explicit timeline entries and evidence links; do not infer or scrape a timeline from external systems. |
| Root cause analysis tools | Recovery and emergency helpers classify failures, but no post-mortem RCA section exists. | Include root-cause categories, contributing factors, detection gaps, and prevention measures in the packet. |
| Action item tracking | Taskmaster and work-tracking can record follow-up work, but this task should not create tickets or mutate Taskmaster automatically. | Include action item entries and recommended follow-up commands; no ticket or Taskmaster mutation. |
| Follow-up automation | Current foundation favors explicit commands and evidence capture. | Represent follow-up automation as a reviewed checklist; do not install schedulers or create external follow-up jobs. |
| Post-mortem metrics | Static metrics can be derived from entered timeline/action data. | Include deterministic counts and duration estimates where input allows. |
| Knowledge extraction | HANDOFF, FINDINGS, DECISIONS, Serena memories, and reports are existing knowledge stores. | Include lessons learned and knowledge-extraction prompts; do not publish to an external knowledge base. |
| Prevention measures tracking | Existing process can capture prevention entries and owner/status fields. | Include prevention measures and verification commands in the packet. |

## Confirmed Current Gap

The foundation can respond to incidents and recover safely, but it has no dedicated command that turns incident facts into an auditable post-mortem packet:

- incident summary, severity, impact, and detection source;
- timeline entries with evidence links;
- root cause and contributing factor analysis;
- action items with owner/status/due-date fields;
- prevention measures with verification commands;
- lessons learned and knowledge extraction;
- static metrics such as action item counts, open prevention counts, and estimated detection/recovery duration;
- explicit non-goals showing that no external incident, ticket, dashboard, notification, scheduler, or Taskmaster mutation was performed.

Without that command, post-mortem work remains a remembered checklist assembled by the current agent.

## Selected Implementation Scope

Add a non-destructive incident post-mortem packet to `scripts/codex-task`:

```bash
python3 scripts/codex-task incident post-mortem \
  --summary "Guard regression after workflow update" \
  --severity P1 \
  --impact "Guard blocked task closeout until evidence was repaired" \
  --timeline "2026-05-13T10:00:00+02:00|Detection|Guard failed during validation|reports/guard.txt" \
  --root-cause "workflow|Missing evidence link in tracker" \
  --action-item "foundation_maintainer|Add regression coverage|open|2026-05-20" \
  --prevention "Run work-tracking audit before guard|python3 scripts/codex-task work-tracking audit" \
  --lesson "Evidence links need to be generated before plan sync" \
  --report-file docs/ai/work-tracking/active/<folder>/reports/post-mortem-process/post-mortem-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/post-mortem-process/post-mortem-YYYY-MM-DD.md
```

The command should:

- write deterministic JSON and optional Markdown outputs;
- snapshot current Git, workflow, Taskmaster, and Serena state using existing helper internals;
- accept explicit repeated timeline, root-cause, action-item, prevention, and lesson entries;
- compute simple static metrics from the supplied entries;
- link recommended follow-up helpers such as recovery, emergency, rollback, change advisory, operational runbook, final validation, guard, audit, and Taskmaster health;
- state clearly that it does not create tickets, send notifications, update dashboards, mutate Taskmaster/session/plan/work-tracking state beyond requested report files, install schedulers, or contact external systems.

## Non-Goals

- No external incident tracker, issue, ticket, dashboard, notification, webhook, email, Slack, PagerDuty, or knowledge-base integration.
- No automatic Taskmaster task creation, status change, or follow-up mutation.
- No timeline scraping from GitHub, CI, logs, sessions, or external services.
- No root-cause inference model or automatic blame assignment.
- No scheduler, daemon, reminder service, or long-running follow-up automation.
- No replacement for emergency, recovery, rollback, change advisory, operational runbook, final validation, Taskmaster health, work-tracking audit, or guard helpers.

## Planned Files

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `reports/README.md`
- `templates/TOOLS.md`
- Task 72 work-tracking artifacts and task-local evidence

## Evidence Plan

- `python3 scripts/codex-task incident post-mortem --summary ... --severity ... --report-file <task-report>.json --runbook-file <task-runbook>.md`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Decision

Proceed with a static incident post-mortem packet command. This satisfies Task 72 by making the post-mortem process executable, portable, and evidence-backed while avoiding fake incident-management infrastructure.

## S:W:H:E

- **2026-05-13 17:20 CEST** - [S:20260513|W:task72-post-mortem-process|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260513-task72-post-mortem-process-ACTIVE/designs/post-mortem-process-scope-reconciliation.md] Reconciled Task 72 from live incident-management wording to a static incident post-mortem packet over existing foundation helpers.
