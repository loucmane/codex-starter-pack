# Task 66 Deprecation Management Scope Reconciliation

**Captured**: 2026-05-13 18:34 CEST  
**Task**: 66 - Setup Deprecation Management

## Historical Task Wording

Task 66 asks for a systematic deprecation process:

- deprecation timeline tracker;
- deprecation warnings in logs;
- grace-period enforcement;
- migration path documentation;
- automatic archival;
- deprecation metrics;
- deprecation notifications;
- emergency deprecation override.

That wording predates the current portable foundation. The repository is now a static, file-backed workflow foundation with Taskmaster state, session/plan/work-tracking evidence, template registry metadata, lifecycle/versioning policies, and deterministic JSON/Markdown review packets. It is not a live service with runtime logs, schedulers, notification systems, external dashboards, or destructive automatic archival.

## Evidence Reviewed

- Task 29 already implemented template lifecycle management:
  - `templates/metadata/template-lifecycle-policy.json`
  - `scripts/template_lifecycle.py`
  - `tests/meta_workflow_guard/test_template_lifecycle.py`
  - lifecycle states, compatibility mappings, transition rules, 30-day grace period, 90-day archive recommendation, replacement/migration notice metadata, semver bumping, and non-mutating registry audit.
- Current lifecycle audit passes: `python3 scripts/template_lifecycle.py audit --today 2026-05-13` reports `226 records, 0 issue(s)`.
- Task 58 already implemented non-mutating template versioning policy, compatibility assessment, history-entry generation, and rollback target data.
- Task 49 already provides repo-native communication templates, including breaking-change and feedback/follow-up communication guidance without external delivery infrastructure.
- Task 57 already provides a static operational runbook composer and explicitly avoids schedulers, tickets, notifications, dashboards, deployment, rollback, and external systems.
- Task 35, Task 44, Task 47, and Task 68 provide emergency, change-advisory, recovery, and final-validation primitives.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 66 Decision |
| --- | --- | --- |
| Deprecation timeline tracker | Lifecycle metadata has `deprecated_since`; versioning helper can emit history entries. | Compose a review packet that surfaces timeline metadata and missing timeline evidence; do not build a new timeline database. |
| Deprecation warnings in logs | `scripts/template_lifecycle.py` emits structured warning/recommendation issues during audit. | Treat audit issues as static warning evidence; do not invent runtime log warnings. |
| Grace-period enforcement | Lifecycle policy has `grace_days` and audit flags expired grace periods. | Surface grace status in static metrics; do not block runtime usage outside existing guard/audit flows. |
| Migration path documentation | Lifecycle metadata supports `replacement` and `migration_notice`; communication guide has breaking-change language. | Require review packet to report missing migration guidance and point to communication templates. |
| Automatic archival | Lifecycle audit can recommend archival after `archive_after_days`. | Keep archival non-destructive and operator-reviewed; no automatic file moves. |
| Deprecation metrics | Lifecycle audit can count records, statuses, warnings, recommendations, expired grace periods, and archive candidates. | Add deterministic metrics to the Task 66 review packet. |
| Deprecation notifications | Communication templates exist, but no email/chat/notification integration exists. | Provide notification guidance and template pointers only; no sending. |
| Emergency override | Emergency/change/recovery helpers exist and repo policies cover explicit bypass documentation. | Include override guidance and required evidence fields; do not create bypass automation. |

## Confirmed Current Gap

The repository has lifecycle and versioning primitives, but no single deprecation-management command that answers:

- How many templates are stable, draft, review/beta, deprecated, archived, or ignored?
- Which deprecated records have grace-period warnings or archive recommendations?
- Which deprecated records are missing replacement or migration notice evidence?
- Which commands refresh lifecycle audit, versioning assessment, communication, operational, and validation evidence?
- Which deprecation actions are operator-reviewed rather than automatic?
- What evidence is required before claiming a deprecation is communicated, migrated, archived, or overridden?

## Selected Implementation Scope

Add a non-destructive deprecation-management review command to `scripts/codex-task`:

```bash
python3 scripts/codex-task deprecation review \
  --label task66-deprecation-management \
  --report-file docs/ai/work-tracking/active/<folder>/reports/deprecation-management/deprecation-review-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/deprecation-management/deprecation-review-YYYY-MM-DD.md
```

The command should:

- snapshot current Git, workflow, Taskmaster, and Serena state;
- load the existing lifecycle policy through `scripts/template_lifecycle.py`;
- run the registry lifecycle audit without mutating templates;
- summarize lifecycle status counts, audit issue counts, grace-period warnings, archive recommendations, and missing migration guidance;
- review supporting evidence domains: lifecycle policy/audit, versioning policy, communication templates, operational runbook, emergency/change/recovery guidance, and final validation;
- list refresh commands for each domain;
- include deprecation action guidance for timeline, warning, grace, migration, archival, notification, override, and closeout review;
- state non-goals explicitly: no runtime log instrumentation, no schedulers, no automatic archival moves, no notifications, no dashboards, no external systems, and no bypass automation.

## Non-Goals

- No destructive automatic archival or file movement.
- No runtime log warning instrumentation.
- No cron, daemon, GitHub scheduled workflow, or background reminder service.
- No email, Slack, chat, ticket, webhook, dashboard, or external notification integration.
- No replacement for `scripts/template_lifecycle.py` or `scripts/template_versioning.py`.
- No mass frontmatter rewrite across `templates/**`.
- No emergency bypass automation; overrides remain explicit, documented workflow decisions.

## Planned Files

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `reports/README.md`
- `templates/TOOLS.md`
- Task 66 work-tracking artifacts and report evidence under `reports/deprecation-management/`

## Verification Plan

- Generate a Task 66 deprecation review JSON/Markdown packet.
- Run focused codex-task tests.
- Run lifecycle regression tests.
- Run plan sync, work-tracking audit, Taskmaster health, guard, and diff-check.

## Decision

Proceed with a static deprecation-management review packet. This satisfies Task 66 by making deprecation status, warning, grace, migration, archival recommendation, communication, and override evidence inspectable without pretending the repository has live logs, notifications, schedulers, dashboards, or automatic destructive archival.
