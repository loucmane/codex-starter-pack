# Task 39 Implement Auto-Fix Mode for Guard – Implementation Notes

## Planned Workstreams
- [x] Add `validate --fix-preview`, `validate --auto-fix`, optional `--fix-kind`, and optional `--fix-history` support to `scripts/codex-guard`.
- [x] Implement the first safe fixer: `tracker-last-updated` for active `TRACKER.md` metadata.
- [x] Ensure auto-fix mode reruns validation after applying fixes and returns success only when remaining guard issues are gone.
- [x] Add focused tests for preview, mutation, selective filtering, history, and remaining non-fixable failures.

## Implemented Behavior
- `--fix-preview` renders supported fixes without writing files and still returns nonzero while guard issues remain.
- `--auto-fix` applies supported fixes, appends JSONL history, reruns validation, and succeeds only when post-fix validation is clean.
- `--fix-kind tracker-last-updated` allows selective execution of the initial safe fixer.
- `--fix-history` allows callers to place applied-fix history in a task-local evidence path when desired; default is `reports/guard-fixes/history.jsonl`.

## Initial Fixer
- `tracker-last-updated` updates or inserts the `**Last Updated**: YYYY-MM-DD` metadata line in active work-tracking `TRACKER.md` files.
- The fixer is intentionally narrow and does not infer evidence, progress entries, Taskmaster state, session state, plan state, or S:W:H:E content.

## Evidence
- Focused tests: `reports/guard-auto-fix-mode/tests-2026-05-11-guard-rules.txt`
- CLI help: `reports/guard-auto-fix-mode/validate-help-2026-05-11.txt`
