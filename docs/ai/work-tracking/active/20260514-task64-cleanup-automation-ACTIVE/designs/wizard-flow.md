# Task 64 Cleanup Automation Scope Reconciliation

## Decision

Task 64 will implement a deterministic, non-destructive cleanup planning packet, not a cron scheduler, automatic deletion system, notification service, rollback executor, or background cleanup daemon.

The historical Taskmaster wording asks for a cleanup scheduler with cron, legacy file detection, safe deletion with backups, audit trail, dry-run mode, metrics, rollback capability, and notifications. In the current portable foundation, destructive cleanup is intentionally manual and evidence-gated. Existing helpers already support scanner outputs, reference-fix dry-runs, backup paths, rollback planning, deprecation review, and work-tracking archive closeout. The current gap is one static cleanup packet that composes those inputs into cleanup candidates and manual approval gates without deleting, moving, notifying, scheduling, or rolling back anything.

## Current Evidence

| Historical Area | Current Evidence | Task 64 Treatment |
| --- | --- | --- |
| Cleanup scheduler with cron | Reports are static and CI-driven; no scheduler policy exists for destructive cleanup | Provide refresh commands and manual cadence guidance; do not install cron. |
| Legacy file detection | `TemplateRegistry`, scanner outputs, Task 108 legacy PROJECT-BLOG cleanup, duplicate/reference reports | List candidate evidence domains and candidate paths; do not auto-delete. |
| Safe deletion with backups | `scripts/template-ssot-scanner/apply_reference_fixes.py` has dry-run, backup, and rollback support for reference fixes | Surface backup/rollback prerequisites; do not execute deletion. |
| Cleanup audit trail | work-tracking archive, session/plan/tracker evidence, Taskmaster health | Require evidence paths and manual approvals before cleanup. |
| Cleanup dry-run mode | scanner/fix helpers support report generation and dry-run patterns | Generate a static cleanup plan; do not mutate source files. |
| Cleanup metrics | template metrics, migration health, deprecation review, Taskmaster health | Provide metrics checklist and refresh commands. |
| Rollback capability | rollback checkpoint/plan helpers and emergency policy | Require checkpoint guidance before cleanup; do not run rollback. |
| Notifications | communication templates and stakeholder packets exist | Draft manual notification guidance only; do not send notifications. |

## Proven Gap

The project has cleanup-adjacent helpers and archived cleanup evidence, but no single artifact that answers:

- Which legacy-artifact and cleanup evidence domains are ready?
- Which cleanup candidate classes should be reviewed manually?
- What evidence must exist before any deletion, archive, or generated-output cleanup is considered?
- Which dry-run, backup, rollback, and approval gates are mandatory?
- Which refresh commands should an operator run before cleanup review?
- Which actions remain manual and out of scope?

## Implementation Boundary

Implement:

- `python3 scripts/codex-task cleanup plan`
- JSON output with label, mode, action boundary, current state, summary, evidence domains, cleanup candidates, approval gates, dry-run checks, backup/rollback guidance, metrics checklist, manual notification guidance, refresh commands, and non-goals
- Markdown output suitable for human review before any cleanup action
- focused parser, builder, renderer, missing-evidence, and handler tests
- `reports/cleanup-automation/README.md`

Do not implement:

- cron jobs, schedulers, daemons, background cleanup, or GitHub scheduled workflows
- automatic deletion, moving, archiving, restoration, rollback, `git clean`, `git reset`, or destructive file operations
- notification delivery, email/chat/webhook/ticket creation, or external service calls
- backup execution, retention-policy enforcement, or automatic candidate approval
- source report, Taskmaster, session, plan, work-tracking, template, Git, or scanner mutations from packet rows

## Packet Model

The cleanup planning packet should expose:

- evidence domains with status, evidence paths, and refresh commands
- cleanup candidate classes with risk, manual action, evidence, and approval requirements
- approval gates before any cleanup action
- dry-run commands and verification commands
- backup and rollback guidance
- metrics checklist for cleanup readiness
- manual notification guidance
- explicit non-goal boundaries

## Acceptance

Task 64 is done when:

- the static cleanup planning packet can be generated locally
- missing source inputs are visible as `needs-evidence`, not fabricated as complete
- focused tests prove parser, builder, renderer, and handler behavior
- final Task 64 evidence includes the sample JSON/Markdown packet, tests, plan sync, work-tracking audit, guard, Taskmaster health, and diff-check
- Taskmaster Task 64 and subtasks are marked done after verification
