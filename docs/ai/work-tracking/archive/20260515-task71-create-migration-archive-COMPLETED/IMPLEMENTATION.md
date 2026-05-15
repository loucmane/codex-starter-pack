# Task 71 Create Migration Archive – Implementation Notes

## Planned Workstreams
- [x] Correct generated plan wording from generic wizard language to migration archive scope.
- [x] Add a scope reconciliation design describing canonical archive locations and non-goals.
- [x] Implement `python3 scripts/codex-task migration archive` as a static archive index/search packet.
- [x] Add focused tests and capture verification evidence.

## Implementation Summary

- Added `migration archive` under the existing `migration` command group in `scripts/codex-task`.
- The command inventories completed work-tracking folders, report families, scanner tools and outputs, plans, Taskmaster task files, Serena memories, decision records, lesson candidates, and a migration timeline.
- The command supports `--query` search filtering through `search_results`.
- JSON output is written only when `--report-file` is supplied; Markdown output is written only when `--runbook-file` is supplied; `--dry-run` prints JSON.
- Non-goals are explicit in the packet: no move/copy/delete/zip/upload/export/publish or external system mutation.

## Evidence

- Archive packet: `reports/migration-archive/migration-archive-2026-05-15.json`
- Archive runbook: `reports/migration-archive/migration-archive-2026-05-15.md`
- Query packet: `reports/migration-archive/migration-archive-search-reference-remediation-2026-05-15.json`
- Focused tests: `reports/migration-archive/tests-2026-05-15-migration-archive-focused.txt`
