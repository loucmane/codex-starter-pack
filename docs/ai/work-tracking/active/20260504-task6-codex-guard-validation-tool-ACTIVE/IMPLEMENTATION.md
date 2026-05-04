# Task 6 Task 6 Codex-Guard Validation Tool – Implementation Notes

## Planned Workstreams
- Scope reconciliation against current `scripts/codex-guard`.
- Identify the real remaining guard gap before implementation.
- Add or adjust focused tests only after the gap is proven.
- Capture real guard/test evidence and final Taskmaster status.

## Implementation Notes

- Implementation is intentionally blocked until `plan-step-scope-audit` is complete.
- Added `.pre-commit-config.yaml`.
- Added local hooks for `python3 scripts/codex-guard validate --include-untracked` and `python3 scripts/codex-guard drift-check --strict --report-dir ""`.
- Set `pass_filenames: false` because guard evaluates repository workflow state from git status, active plan, session, tracker, and configured roots rather than individual file arguments.
- Set `always_run: true` so local hook behavior mirrors CI enforcement.
- Disabled local drift report output so pre-commit does not mutate the working tree; CI/report commands still write artifacts.
- Added regression coverage that verifies the pre-commit config keeps both guard commands wired.
