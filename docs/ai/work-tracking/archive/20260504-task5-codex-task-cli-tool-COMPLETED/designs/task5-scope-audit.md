# Task 5 Scope Audit

**Date**: 2026-05-04 11:32 CEST
**Task**: Task 5 - Implement Codex-Task CLI Tool
**Branch**: `feat/task-5-codex-task-cli-tool`

## Current-State Finding

Task 5 is not a greenfield CLI build anymore. Later foundation tasks already produced a substantial `scripts/codex-task` helper with session logging, work-tracking operations, plan sync, bootstrap, wizard kickoff, scanner orchestration, S:W:H:E logging, and dry-run support.

## Requirement Matrix

| Historical Task 5 Detail | Current Evidence | Status |
|--------------------------|------------------|--------|
| Create `scripts/codex-task` | `scripts/codex-task` exists and is tested by `tests/meta_workflow_guard/test_codex_task.py` | Already done |
| Use Click framework | Current helper uses `argparse`; replacing it would be churn without a current functional gap | Not pursued |
| `sessions update` command | `codex-task sessions update` exists | Already done |
| `scanner run --log-note` command | `codex-task scanner run ... --log-note` exists | Already done |
| S:W:H:E structured logging | Session, tracker, scanner, and work-tracking update helpers emit S:W:H:E entries | Already done |
| Git/session detection | Current session resolution, branch validation, and wizard kickoff logic exist | Already done |
| `--dry-run` for destructive operations | Top-level dry-run is honored by scaffold/archive/update/bootstrap/wizard/report paths where applicable | Already done / preserved |
| Rich progress bars | No current long-running `codex-task` workflow needs progress bars; adding Rich would introduce dependency/UI churn | Not pursued |
| `report generate` command | No `report` subcommand existed before this task | Implemented gap |

## Implemented Gap

Added `codex-task report generate` as a thin orchestration layer over the existing report generators:

- `--kind metrics` runs `scripts/template-metrics-dashboard`.
- `--kind drift` runs `scripts/codex-guard drift-check`.
- `--kind all` runs drift first, then metrics.
- `--strict-drift` forwards strict drift handling to `codex-guard`.
- `--dry-run` prints the commands without executing them.

## Verification Evidence

- Parser/help: `python3 scripts/codex-task report generate --help`
- Dry-run: `python3 scripts/codex-task --dry-run report generate --kind all --strict-drift`
- Unit tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- Real report run: `docs/ai/work-tracking/active/20260504-task5-codex-task-cli-tool-ACTIVE/reports/report-generate-2026-05-04.txt`

## Decision

Task 5 should be completed by adding the missing report command and tests, not by rewriting the existing CLI in Click or adding Rich progress bars without a current user-facing workflow that needs them.
