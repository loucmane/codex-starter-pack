# Emergency Response Runbook

- Incident ID: 20260510-130847-task35-foundation-response
- Label: task35-foundation-response
- Created at: 2026-05-10T13:08:47+02:00
- Mode: non-destructive-emergency-response-plan
- Executes actions: False
- Severity: P1 - High-risk workflow regression
- Summary: Task 35 emergency response planner verification

## Classification

- Description: A core foundation gate, helper, or generated artifact is degraded but safe inspection and scoped remediation remain possible.
- Response SLA: 30 minutes
- Review SLA: 48 hours

Examples:
- guard behavior regresses on a feature branch
- Taskmaster health reports invalid dependency references
- work-tracking audit reports multiple active folders or stale current pointers

## Halt Guidance

- Halt recommended: True
- Automatic halt: False

- Stop implementation and switching tasks until current state is inspected.
- Do not run reset, clean, restore, branch deletion, rollback, or force-push commands automatically.
- Capture a rollback checkpoint before remediation if the working tree or workflow state is dirty.
- Record the incident response plan and decision in the active work-tracking folder before continuing.

## Current State Snapshot

- Branch: feat/task-35-emergency-response-system
- HEAD: d733bca5ab473a89343cf6d363f7a8a06ed251ca
- Dirty status entries: 13
- Current session: sessions/2026/05/2026-05-10-002-task35-emergency-response-system.md
- Current plan: plans/2026-05-10-task35-emergency-response-system.md
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260510-task35-emergency-response-system-ACTIVE']

## Response Checklist

### Confirm repository and workflow state

- ID: confirm-state

- `git status --short --branch`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`

### Run foundation safety gates

- ID: run-foundation-gates

- `python3 scripts/codex-guard validate --include-untracked`
- `python3 scripts/codex-task report generate --kind all`
- `git diff --check`

### Capture rollback context when remediation may touch tracked state

- ID: capture-rollback-context

- `python3 scripts/codex-task rollback checkpoint --label <incident-label> --report-file <checkpoint.json>`
- `python3 scripts/codex-task rollback plan --snapshot <checkpoint.json> --report-file <recovery-plan.md>`

### Prepare repository-native communication

- ID: communicate-status

- Use templates/guides/communication/foundation-communication-templates.md

## Escalation Guidance

- repo_native: Record severity, current state, decisions, and next steps in the active work-tracking folder and session log.
- external_integrations: No PagerDuty, Slack, email, or chat webhook integration is configured by this policy.
- owner_review: For P0/P1, require explicit user review before remediation commands that mutate Git, Taskmaster, sessions, plans, work-tracking, or generated reports.

## Post-Incident Review

- What happened?
- What triggered detection?
- Which gates or evidence caught it?
- Which mutation surfaces were blocked or allowed?
- What remediation was performed?
- What follow-up task or guard should prevent recurrence?

## Recommended Verification Commands

- `git status --short --branch`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `python3 scripts/codex-task report generate --kind all`
- `git diff --check`

## Non-Goals

- No external incident service is configured.
- No notification is sent.
- No dashboard is updated.
- No halt marker is written automatically.
- No rollback, reset, clean, restore, branch deletion, or force push is executed.
- No emergency response command was executed by this planner.
- No rollback, reset, clean, restore, branch deletion, notification, dashboard update, or external incident action was executed.

No halt, notification, rollback, reset, cleanup, dashboard update, or external incident action was executed by this plan.
