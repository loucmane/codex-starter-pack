# Task 44 Setup Change Advisory Board Process – Implementation Notes

## Planned Workstreams
- Scope reconciliation: completed in `designs/change-advisory-scope-reconciliation.md`.
- Helper: added `python3 scripts/codex-task change advisory` to emit a non-destructive JSON packet and Markdown runbook.
- Tests: added parser, packet-building, runbook-rendering, and output-writing coverage to `tests/meta_workflow_guard/test_codex_task.py`.
- Evidence: generate Task 44 advisory JSON/runbook and capture focused tests, plan sync, audit, health, guard, and diff-check logs under `reports/change-advisory-board-process/`.

## Implemented Behavior
- Reuses `scripts/template_governance.py` and `templates/metadata/template-governance-policy.json` for review classes, roles, approval guidance, notification audiences, and required evidence.
- Supports automatic governance assessment from version/lifecycle/emergency signals or explicit `--review-class` override.
- Snapshots current Git, workflow, Taskmaster, and Serena state.
- Renders advisory controls, communication guidance, post-implementation review prompts, recommended verification commands, and explicit non-goals.
- Writes JSON and Markdown outputs only when `--report-file` and/or `--runbook-file` are supplied; otherwise it prints the runbook or dry-run JSON.
- Performs no CAB meetings, votes, approvals, notifications, dashboards, deployments, rollback, cleanup, or external tracking actions.
