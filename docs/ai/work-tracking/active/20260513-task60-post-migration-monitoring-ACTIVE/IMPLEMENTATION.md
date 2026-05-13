# Task 60 Setup Post-Migration Monitoring – Implementation Notes

## Planned Workstreams
- [x] Scope reconciliation
  - Confirmed Task 17, Task 37, Task 41, and Task 55 already cover static monitoring, telemetry, migration health, and migration KPIs.
  - Reframed Task 60 to a post-migration monitoring packet and cadence runbook instead of live observability infrastructure.
- [x] CLI implementation
  - Added `python3 scripts/codex-task migration monitoring`.
  - The command reads a migration metrics JSON packet plus a migration-health JSON report.
  - It writes deterministic JSON and Markdown reports with aggregate status, required actions, source highlights, weekly/monthly/quarterly/yearly cadence checks, automation guidance, and explicit non-goals.
  - The command is non-destructive and performs no scheduling, alert delivery, production checks, scanner regeneration, or remediation mutation.
- [x] Documentation
  - Added `reports/post-migration-monitoring/README.md`.
  - Updated `reports/README.md` and `templates/TOOLS.md` to describe the new static monitoring packet.
- [x] Tests and task-local evidence
  - Added parser, report-builder, missing-input, renderer, handler, and strict-mode coverage in `tests/meta_workflow_guard/test_codex_task.py`.
  - Captured focused pytest and report-generation evidence under `reports/post-migration-monitoring/`.

## Generated Evidence

- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/tests-2026-05-13-codex-task.txt`
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/source-migration-health-2026-05-13.txt`
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/source-migration-health/latest.json`
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/source-migration-health/latest.md`
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/post-migration-monitoring-2026-05-13.txt`
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/post-migration-monitoring-2026-05-13.json`
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/post-migration-monitoring-2026-05-13.md`

## Result

The generated post-migration monitoring packet reports aggregate status `fail`. This is expected and honest because the Task 55 migration metrics packet still contains real migration blockers, while the migration-health source report is `warn` due to missing optional static telemetry inputs. Task 60 implements monitoring/reporting, not remediation.
