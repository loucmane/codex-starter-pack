# Task 95 Template Drift Detection – Implementation Notes

## Planned Workstreams
- Add a `drift-check` subcommand to `scripts/codex-guard`.
- Build a report model covering canonical-doc drift, template metadata drift, and explicitly mapped workflow-surface drift.
- Write repo-level drift outputs under `reports/template-drift/` and store task-local verification artifacts under the Task 95 active folder.
- Extend `tests/meta_workflow_guard` with focused drift-detection coverage.
- Document the expected CI or scheduled-run automation path for the new reports.

## Completed Workstreams
- Added `drift-check` to `scripts/codex-guard` with strict-mode exit handling and automatic text/JSON report generation.
- Reused the existing template metadata and canonical GAC guidance validators so drift-check stays aligned with the live enforcement rules.
- Added repo-level report documentation in `reports/template-drift/README.md`.
- Added unit coverage for metadata drift, canonical-doc drift, command-surface drift, and report writing.
- Updated both guard workflows to run `python3 scripts/codex-guard drift-check --strict` and upload the generated drift artifacts.
