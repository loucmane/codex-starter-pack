# Template Usage Analytics Reports

This directory stores static template usage analytics generated from the template registry and workflow evidence.

```bash
python3 scripts/codex-task template usage-analytics \
  --report-file reports/template-usage-analytics/latest.json \
  --runbook-file reports/template-usage-analytics/latest.md
```

## Output Files

- `latest.json` - machine-readable usage analytics payload
- `latest.md` - human-readable usage analytics report

## Scope

The report loads registered templates through `TemplateRegistry` and scans static workflow sources:

- `sessions/`
- `plans/`
- active work-tracking folders
- `.taskmaster/tasks/`
- archived work-tracking folders only when `--include-archive` is passed

It counts registry ID, template path, and alias references, then summarizes source coverage, category usage, top templates, path-only references, alias references, zero-observed-reference templates, and static review guidance.

The report does not add runtime decorators, create a database, run a live dashboard, send alerts, train predictive models, mutate templates, or contact external analytics services.
