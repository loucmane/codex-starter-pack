# Task 15 Serena Integration

## Context
- Branch: `feat/task-15-serena-integration-template-system`
- Active session: `sessions/2026/05/2026-05-08-005-task15-serena-integration-template-system.md`
- Active plan: `plans/2026-05-08-task15-serena-integration-template-system.md`
- Active tracker: `docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/TRACKER.md`

## Scope Decision
Task 15 historical wording said template discovery, analysis, and evidence should always route through Serena MCP. Current repository evidence shows the correct contract is capability-aware: deterministic template lookup remains registry/scanner first; Serena is mandatory for memory continuity, semantic inspection when the runtime exposes the tools, and structured fallback evidence for unresolved template queries.

## Implementation So Far
- Added project-level `serena` MCP entry to `.mcp.json`, matching the pinned `uvx ... serena start-mcp-server --project-from-cwd` command in `.codex/config.toml`.
- Added `python3 scripts/codex-task serena status --strict [--report-file <path>]` to verify Codex config, project MCP config, and `.serena/memories/` readiness.
- Added focused helper tests in `tests/meta_workflow_guard/test_codex_task.py` for parser acceptance, strict pass, and missing project MCP failure.
- Updated Serena/tooling/work-tracking docs to distinguish deterministic registry/scanner/`rg` evidence from Serena semantic and memory evidence.
- Completed Taskmaster subtask `15.1` and refreshed only `.taskmaster/tasks/task_015.txt`.

## Evidence
- Scope reconciliation: `docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/designs/serena-integration-scope-reconciliation.md`
- Serena status report: `docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/reports/serena-integration-template-system/serena-status-2026-05-08.txt`
- Focused test report: `docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/reports/serena-integration-template-system/tests-2026-05-08-codex-task.txt`

## Next Steps
- Run final plan sync, work-tracking audit, guard, diff-check, and any broader focused tests.
- Mark `15.2` done after final verification and regenerate only Task 15.
- Update tracker/session/handoff with final evidence and open PR.