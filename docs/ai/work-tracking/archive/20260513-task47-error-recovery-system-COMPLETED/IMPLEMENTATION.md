# Task 47 Build Error Recovery System – Implementation Notes

## Planned Workstreams
- Add `python3 scripts/codex-task recovery plan`.
- Generate deterministic JSON and Markdown artifacts with error classification, context snapshot, backoff guidance, recovery steps, escalation guidance, verification commands, and non-goals.
- Reuse existing Git/workflow/Taskmaster/Serena snapshot helpers.
- Keep the helper non-destructive: no retry, rollback, reset, cleanup, notification, dashboard update, or external recovery action is executed.

## Implemented
- Added `ERROR_RECOVERY_TAXONOMY` with guard, Taskmaster, Git, MCP, validation, security, config, transient, and monitoring classes.
- Added `_build_error_recovery_plan` to produce a deterministic, non-destructive JSON plan with Git/workflow/Taskmaster/Serena context, retry policy, decision path, recovery steps, verification commands, related helper references, and explicit non-goals.
- Added `_render_error_recovery_runbook` for Markdown runbooks that mirror the JSON plan and make non-execution explicit.
- Added `python3 scripts/codex-task recovery plan` with `--error-class`, `--summary`, optional label/backoff controls, `--report-file`, `--runbook-file`, and `--dry-run`.
- Added focused tests covering parser wiring, plan classification, unknown-class rejection, runbook rendering, and JSON/Markdown file output.

## Evidence
- Focused tests: `docs/ai/work-tracking/active/20260513-task47-error-recovery-system-ACTIVE/reports/error-recovery-system/tests-codex-task-2026-05-13.txt` (`78 passed`)
- Live JSON plan: `docs/ai/work-tracking/active/20260513-task47-error-recovery-system-ACTIVE/reports/error-recovery-system/recovery-plan-2026-05-13.json`
- Live Markdown runbook: `docs/ai/work-tracking/active/20260513-task47-error-recovery-system-ACTIVE/reports/error-recovery-system/recovery-runbook-2026-05-13.md`

## Non-Goals Preserved
- No automatic retry loop is executed.
- No rollback, reset, clean, restore, branch deletion, or force push is executed.
- No Taskmaster, session, plan, or work-tracking state is changed by the helper beyond explicitly requested report files.
- No notification, dashboard update, external ticket, incident integration, or external recovery service is triggered.
