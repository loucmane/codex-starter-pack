# Post-Migration Monitoring Reports

This directory stores optional static post-migration monitoring packets produced by:

```bash
python3 scripts/codex-task migration monitoring
```

## Output Files

The command can write task-local or repo-level artifacts:

- `latest.json` - machine-readable monitoring packet when callers choose this directory
- `latest.md` - human-readable monitoring runbook when callers choose this directory

Task-specific evidence should usually be written under the active work-tracking folder:

```text
docs/ai/work-tracking/active/<YYYYMMDD-task-slug-ACTIVE>/reports/post-migration-monitoring/
```

## Scope

The packet reads the migration KPI report from `python3 scripts/codex-task migration metrics` and the aggregate migration-health report from `reports/migration-health/latest.json`. It turns those inputs into:

- pass/warn/fail post-migration monitoring status;
- required follow-up actions for missing, warning, or failing source reports;
- weekly scanner-health checks;
- monthly usage/cost reviews;
- quarterly benchmark reviews;
- yearly roadmap/planning reviews;
- exact refresh commands and expected evidence.

The implementation is static and file-based. It does not install a scheduler, start a daemon, send alerts, create tickets, contact production services, mutate scanner outputs, or apply remediations.
