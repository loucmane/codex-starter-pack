# Task 143 Dogfood reconcile promotion criteria – Implementation Notes

## Planned Workstreams
- Create safe disposable fixture histories under `/tmp`.
- Capture `aegis reconcile` raw text and JSON output for squash-shaped, true-drift, and ambiguity/stub-heavy target histories.
- Capture before/after status snapshots proving reconcile does not mutate targets.
- Classify every finding and notable non-finding for operator signal quality.
- Define promotion criteria for any later auto-mutation task while keeping Task 143 report-first.

## Completed Evidence
- `squash-offline-no-github.payload.json`: `clean`, 1 task, 0 findings; squash-shaped non-ancestor branch remains unknown in no-GitHub mode.
- `drift-mixed-no-github.payload.json`: `drift`, 1 high-confidence `merged_but_not_done` finding.
- `drift-mixed-github.payload.json`: `drift`, 2 high-confidence findings: `merged_but_not_done` and `done_but_not_merged`.
- `ambiguity-stubs-no-github.payload.json`: `needs_review`, 3 warning-only findings.
- `ambiguity-stubs-github.payload.json`: `needs_review`, 4 warning-only findings including `multi_pr_epic_ambiguity`.
- `promotion-criteria-summary.md`: operator signal-quality assessment and explicit promotion criteria.

## Verification
- `python3 scripts/codex-task work-tracking audit`: passed after Serena memory was captured and logged.
- `python3 scripts/codex-guard validate`: passed after plan sync.
- `python3 scripts/codex-task taskmaster health`: passed before task completion.
- Taskmaster Task 143 was then marked done and `.taskmaster/tasks/task_143.md` was regenerated with `generate-one`.
