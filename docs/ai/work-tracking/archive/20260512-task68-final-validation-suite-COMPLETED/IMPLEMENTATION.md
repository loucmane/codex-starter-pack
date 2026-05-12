# Task 68 Implement Final Validation Suite – Implementation Notes

## Planned Workstreams
- Add a `validation final-suite` subcommand to `scripts/codex-task`.
- Define final-validation requirement coverage and command ordering from the current foundation validators.
- Capture per-check stdout/stderr logs when execute mode is used, continue through failures, then fail unless `--allow-failures` is explicit.
- Render a JSON summary plus Markdown sign-off runbook.
- Add focused parser, plan-building, rendering, execution, and failure tests in `tests/meta_workflow_guard/test_codex_task.py`.
- Update foundation adoption guidance to point final sign-off at the suite command.

## Completed Implementation
- `scripts/codex-task validation final-suite` now supports dry-run planning, execute mode, scoped pytest targets, `--skip-pytest` rehearsal mode, and `--allow-failures` for explicit evidence collection without a hard failure.
- The suite maps Task 68 requirements to current validators and runs 12 checks: Git status, Taskmaster health, plan sync, work-tracking audit, Codex guard, template drift, scanner suite, reference-fix gate, static report pipeline, agent compatibility, pytest, and diff-check.
- Per-check stdout/stderr logs are captured under the suite evidence directory, and generated drift/metrics/monitoring/Phase 0/performance/cost/compatibility reports are kept inside that directory.
- The Markdown runbook includes requirement coverage, check status/evidence, commands, sign-off checklist, and non-goals.
- Focused tests cover parser wiring, manifest construction, runbook rendering, execute-mode evidence capture, and failure-after-evidence behavior.
