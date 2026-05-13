# Task 51 Template Usage Analytics – Implementation Notes

## Planned Workstreams
- Scope reconciliation against the current portable foundation.
- Static usage analytics command implementation.
- Focused parser, builder, renderer, archive-option, and output tests.
- Task-local evidence and final guard/audit/Taskmaster verification.

## Implemented Command

```bash
python3 scripts/codex-task template usage-analytics \
  --label <label> \
  --report-file <usage-analytics.json> \
  --runbook-file <usage-analytics.md>
```

## Behavior

- Loads registered templates via `TemplateRegistry`.
- Scans `sessions/`, `plans/`, active work-tracking, and `.taskmaster/tasks/`.
- Includes archived work-tracking only when `--include-archive` is passed.
- Counts registry ID, template path, and standalone alias mentions.
- Emits source summaries, category summaries, monthly trend counts, top-template summaries, path-only/alias/zero-observed-reference review queues, and explicit non-goals.
- Does not mutate templates, create runtime tracking, start dashboards, send alerts, train predictive models, or contact external services.

## Files Updated

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `reports/template-usage-analytics/README.md`
- `reports/README.md`
- `templates/TOOLS.md`

## Evidence

- Focused tests: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/tests-2026-05-13-codex-task.txt` -> 108 passed.
- Live report: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/template-usage-analytics-2026-05-13.json`.
- Live runbook: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/template-usage-analytics-2026-05-13.md`.
- Plan sync: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/plan-sync-2026-05-13.txt`.
- Work-tracking audit: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/work-tracking-audit-2026-05-13.txt`.
- Taskmaster health: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/taskmaster-health-2026-05-13.txt`.
- Guard: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/guard-2026-05-13.txt`.
- Diff-check: `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/diff-check-2026-05-13.txt`.
