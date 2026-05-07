# Taskmaster Integration Scope Reconciliation

**Captured**: 2026-05-07 15:21 CEST
**Task**: 12 - Setup Taskmaster Integration

## Historical Task Wording

Task 12 originally says to initialize Taskmaster, configure `.taskmaster/config.json`, parse a PRD, configure MCP, configure models, create task templates, and set up dependencies.

That wording is historical. The current repository already has:

- `.taskmaster/tasks/tasks.json`
- generated task files under `.taskmaster/tasks/`
- `.taskmaster/config.json`
- `.mcp.json` with `task-master-ai@latest`
- targeted generated-file refresh via `python3 scripts/codex-task taskmaster generate-one --id <id>`
- workflow scaffolding through `python3 scripts/codex-task wizard kickoff`
- guard coverage for Taskmaster mutations through session/tracker evidence

## Current Evidence

Commands run during scope reconciliation:

- `task-master show 12`
- `task-master validate-dependencies`
- `task-master list`
- `task-master list --status=pending`
- `task-master --version`
- `python3 scripts/codex-task taskmaster health --report-file docs/ai/work-tracking/active/20260507-task12-taskmaster-integration-ACTIVE/reports/taskmaster-integration/taskmaster-health-2026-05-07.txt`

Observed state:

- Taskmaster CLI version: `0.43.1`
- Full dashboard: 107 tasks, 38 done, 1 in progress, 68 pending
- Full dependency validation: 107 tasks and 302 subtasks checked; no invalid dependencies
- Current Task 12 dependency on Task 1 is valid because Task 1 exists and is done
- Filtered pending list prints 33 invalid dependency warnings because dependencies outside the filtered pending subset are hidden

## Actual Gap

The repo does not need Taskmaster re-initialization.

The proven current-state gap is **operator clarity for Taskmaster dependency health**:

- `task-master validate-dependencies` gives authoritative full-graph health.
- `task-master list` gives the correct full dashboard.
- `task-master list --status=pending` can show misleading invalid dependency warnings because done/in-progress dependency tasks are filtered out of the displayed set.

Future sessions need a deterministic helper and documentation path that distinguishes real dependency corruption from filtered-view warnings.

## Decision

Implement a narrow helper:

```bash
python3 scripts/codex-task taskmaster health \
  --report-file docs/ai/work-tracking/active/<folder>/reports/taskmaster-integration/taskmaster-health-YYYY-MM-DD.txt
```

The helper reads `.taskmaster/tasks/tasks.json` directly, validates the full graph, reports task/subtask/status/dependency counts, and documents the filtered-list caveat.

Do not run `task-master init`, `task-master parse-prd`, broad `task-master generate`, or dependency repair commands for Task 12. There is no evidence those are needed.

## Completion Boundary

Task 12 is complete when:

- `codex-task taskmaster health` exists and is tested;
- the live health report shows zero invalid dependency references;
- Taskmaster workflow docs mention the helper and filtered-list caveat;
- Taskmaster subtasks 12.1/12.2 and parent Task 12 are marked done;
- plan sync, work-tracking audit, guard, and diff-check pass.

