# Task 98 Repo Structure Configuration Contract

## Objective

Move hardcoded repository layout assumptions out of `scripts/codex-guard`, `scripts/codex-task`, and related helpers so the workflow foundation can adapt to repositories that do not use this exact path layout.

## Existing Hardcoded Assumptions

The current automation layer assumes these repo roots:

- `templates/`
- `sessions/`
- `plans/`
- `.plan_state/`
- `.taskmaster/`
- `docs/ai/work-tracking/`
- `reports/`

Those roots are currently baked into:

- `scripts/codex-guard`
- `scripts/codex-task`
- `scripts/template-metrics-dashboard`
- tests that assume the same default structure

## Configuration Source

Use the existing repo-local `.codex/config.toml` as the source of truth. Add a dedicated section:

```toml
[repo_structure]
templates_root = "templates"
sessions_root = "sessions"
plans_root = "plans"
plan_state_dir = ".plan_state"
taskmaster_root = ".taskmaster"
work_tracking_root = "docs/ai/work-tracking"
reports_root = "reports"
```

## Derived Paths

The scripts should derive concrete locations from those roots instead of hardcoding them:

- `sessions/current`
- `sessions/state.json`
- `plans/current`
- `.plan_state/sync.log`
- `.taskmaster/tasks/tasks.json`
- `docs/ai/work-tracking/active/`
- `docs/ai/work-tracking/archive/`
- `reports/template-drift/`
- `reports/template-metrics/`
- `reports/session-continuation/`
- `templates/metadata/template-metadata-policy.json`

## Implementation Boundary

- Keep current paths as defaults so this repo remains unchanged after the refactor.
- Make the scripts read repo-local config once and derive operational paths from it.
- Keep message text and evidence paths aligned with the configured structure where practical.
- Do not try to solve cross-project bootstrap or migration in Task 98; that belongs to Tasks 99-102.

## Initial Inventory

### `scripts/codex-guard`
- active/archive work-tracking roots
- session/current and session state files
- plan/current and plan sync log
- template metadata policy path
- continuation guard directory
- Taskmaster tasks path regex

### `scripts/codex-task`
- sessions root
- plans root
- plan state directory
- active work-tracking root
- Taskmaster tasks directory
- generated session/tracker evidence paths

### `scripts/template-metrics-dashboard`
- Taskmaster JSON
- plan sync log
- drift report directory
- active/archive work tracking roots
- sessions root
- metrics report directory

## Verification Targets

- Scripts still pass with the default repo structure.
- A temp repo-root override in tests proves the loader respects `.codex/config.toml`.
- Task 98 work-tracking and plan evidence use the corrected repo-structure scope.
