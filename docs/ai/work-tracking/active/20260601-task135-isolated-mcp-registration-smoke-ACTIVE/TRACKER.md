# Task 135 Add Isolated Native MCP Registration Smoke Command for Aegis Tracker

**Started**: 2026-06-01
**Status**: COMPLETE
**Last Updated**: 2026-06-01

## Goals
- [x] Add repeatable isolated native MCP registration smoke command
- [x] Verify Codex and Claude temp-home registration without touching real config
- [x] Document and test private GitHub pinned-tag smoke flow

## Progress Log
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:task-master:add-task|E:.taskmaster/tasks/task_135.md] Created Taskmaster Task 135 for isolated native MCP registration smoke tooling
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Task 135 in-progress and refreshed `.taskmaster/tasks/task_135.md`
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:plan|E:plans/2026-06-01-task135-isolated-mcp-registration-smoke.md] Created Task 135 plan and current session pointers
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:apply_patch|E:aegis_foundation/mcp_registration.py] Added isolated native MCP registration smoke helper with temp HOME/XDG/CODEX_HOME handling, register+verify execution, JSON/Markdown report writers, and missing-client skip semantics
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:apply_patch|E:aegis_foundation/cli.py] Added package CLI `aegis mcp smoke-registration`
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:apply_patch|E:scripts/codex-task] Mirrored `aegis mcp smoke-registration` in the repo-local wrapper and synced packaged script assets
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:smoke-registration|E:docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/native-smoke.json] Real Codex and Claude isolated-home smoke registration passed against private GitHub tag `aegis-private-github-20260531`
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:serena/memory|E:memories/2026-06-01_task135_isolated_mcp_registration_smoke] Wrote continuation memory for Task 135 implementation and verification state
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:pytest|E:tests/meta_workflow_guard/test_aegis_native_mcp_registration.py] Focused native registration and release-distribution tests passed: 45 passed, 2 expected skips
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:pytest|E:tests/meta_workflow_guard/test_aegis_installer.py] Broader Aegis contract subset passed: 158 passed, 3 expected env-gated skips
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:codex-guard|E:scripts/codex-guard] Guard validation passed after archiving completed Task 134 work-tracking and syncing the Task 135 plan
- **2026-06-01** — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:task-master:set-status|E:.taskmaster/tasks/task_135.md] Marked Taskmaster Task 135 done and refreshed its generated task file

## Plan Compliance Checklist
- [x] plan-step-scope — Define isolated native MCP registration smoke contract and safety invariants
- [x] plan-step-implement — Update workflow/guard/docs and capture tests
- [x] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
