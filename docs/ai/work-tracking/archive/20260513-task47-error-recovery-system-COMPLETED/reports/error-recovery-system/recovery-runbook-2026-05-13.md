# Error Recovery Runbook

- Recovery ID: 20260513-113717-task47-guard-recovery
- Label: task47-guard-recovery
- Created at: 2026-05-13T11:37:17+02:00
- Mode: non-destructive-error-recovery-plan
- Executes actions: False
- Error class: guard - Guard or workflow policy failure
- Severity: P1
- Summary: Guard failed after workflow date rollover
- Operator message: A foundation guard blocked progress; inspect the workflow state and fix evidence or policy drift before retrying.

## Current State Snapshot

- Branch: feat/task-47-error-recovery-system
- HEAD: 929e58f6982b03b316c7c1f313b144b9c85120aa
- Dirty status entries: 11
- Current session: sessions/2026/05/2026-05-13-002-task47-error-recovery-system.md
- Current plan: plans/2026-05-13-task47-error-recovery-system.md
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260513-task47-error-recovery-system-ACTIVE']

## Retry And Backoff Guidance

- Retryable: False
- Automatic retry: False
- No retry schedule; treat this class as requiring reviewed remediation.

## Decision Path

- Classify the error and confirm whether it is retryable.
- Capture current Git, workflow, Taskmaster, and Serena context.
- Run the recommended evidence commands for this error class.
- If severity is P0 or P1, render an emergency response plan before remediation.
- If remediation may touch tracked state, capture a rollback checkpoint and reviewed recovery plan.
- Document findings, decisions, and final evidence before continuing.

## Recommended Recovery Steps

- Read the guard failure and identify the exact missing or stale workflow artifact.
- Repair session, plan, tracker, Taskmaster, or evidence state with explicit entries.
- Rerun guard and preserve the passing evidence before committing.

## Recommended Verification Commands

- `git status --short --branch`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`
- `python3 scripts/codex-task plan sync`

## Related Helpers

- rollback_checkpoint: `python3 scripts/codex-task rollback checkpoint --label <label> --report-file <checkpoint.json>`
- rollback_plan: `python3 scripts/codex-task rollback plan --snapshot <checkpoint.json> --report-file <recovery-plan.md>`
- emergency_plan: `python3 scripts/codex-task emergency plan --severity <P0-P3> --summary <summary> --report-file <emergency.json> --runbook-file <emergency.md>`
- monitoring: `python3 scripts/template-monitoring --strict`
- final_validation: `python3 scripts/codex-task validation final-suite --dry-run`

## Non-Goals

- No automatic retry loop is executed.
- No rollback, reset, clean, restore, branch deletion, or force push is executed.
- No Taskmaster, session, plan, or work-tracking state is changed beyond requested report files.
- No notification, dashboard update, external ticket, or incident integration is triggered.
- No external recovery service is configured.

No retry, rollback, reset, cleanup, notification, dashboard update, or external recovery action was executed by this plan.
