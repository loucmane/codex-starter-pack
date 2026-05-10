# Cost Tracking Report

Generated: 2026-05-10T13:42:09+02:00
Policy version: 1.0.0
Status: warn
Usage source: none
Executes external actions: False

## Summary
- Total categories: 4
- Passed: 0
- Warnings: 0
- Errors: 0
- Not measured: 4

## Categories
### AI-assisted Taskmaster and research commands

- ID: `ai_taskmaster_commands`
- Status: `not-measured`
- Severity: `warning`
- Unit: `usd`
- Monthly budget: `75.00 usd`
- Warning threshold: `60.00 usd`
- Critical threshold: `75.00 usd`
- Actual: `n/a`
- Projected monthly: `n/a`
- Evaluated amount: `n/a`
- Budget ratio: `n/a`
- Telemetry: manual-or-provider-dashboard
- Source: missing
- Message: No usage input supplied for this category; budget status cannot be claimed.

Review commands:
- `task-master models`
- `task-master complexity-report`

Notes:
- This repository does not query provider billing APIs.
- Supply usage JSON from provider dashboards or a local ledger when you want budget classification.

### GitHub Actions CI minutes

- ID: `github_actions_minutes`
- Status: `not-measured`
- Severity: `warning`
- Unit: `minutes`
- Monthly budget: `1000.00 minutes`
- Warning threshold: `800.00 minutes`
- Critical threshold: `1000.00 minutes`
- Actual: `n/a`
- Projected monthly: `n/a`
- Evaluated amount: `n/a`
- Budget ratio: `n/a`
- Telemetry: github-billing-dashboard
- Source: missing
- Message: No usage input supplied for this category; budget status cannot be claimed.

Review commands:
- `gh run list --limit 20`
- `gh run view <run-id> --log`

Notes:
- GitHub billing/minute totals are account-level data and are not available from local repo files.
- Keep matrices focused and upload artifacts intentionally.

### Local agent runtime and verification effort

- ID: `local_agent_runtime`
- Status: `not-measured`
- Severity: `warning`
- Unit: `hours`
- Monthly budget: `40.00 hours`
- Warning threshold: `32.00 hours`
- Critical threshold: `40.00 hours`
- Actual: `n/a`
- Projected monthly: `n/a`
- Evaluated amount: `n/a`
- Budget ratio: `n/a`
- Telemetry: manual-work-log
- Source: missing
- Message: No usage input supplied for this category; budget status cannot be claimed.

Review commands:
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task report generate --kind all`

Notes:
- This category is useful for monthly process review; it does not control local CPU use.

### Report artifact storage

- ID: `report_storage`
- Status: `not-measured`
- Severity: `warning`
- Unit: `mb`
- Monthly budget: `500.00 mb`
- Warning threshold: `400.00 mb`
- Critical threshold: `500.00 mb`
- Actual: `n/a`
- Projected monthly: `n/a`
- Evaluated amount: `n/a`
- Budget ratio: `n/a`
- Telemetry: repo-local-or-ci-artifact-review
- Source: missing
- Message: No usage input supplied for this category; budget status cannot be claimed.

Review commands:
- `du -sh reports docs/ai/work-tracking 2>/dev/null || true`

Notes:
- The portable foundation keeps evidence by default; storage policy should be reviewed before pruning artifacts.

## Recommended Review Commands

- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task report generate --kind all`
- `git diff --check`

## Non-Goals

- No external billing API is queried.
- No provider dashboard, GitHub billing page, cloud account, or payment system is modified.
- No alert, notification, issue, email, PagerDuty, or Slack message is sent.
- No cache, rate limit, throttle, branch protection, or workflow state is changed based on this report.
- No cost claim is made for categories without supplied usage data.

No external billing query, alert delivery, cache mutation, rate-limit change, or throttling action was executed by this report.
