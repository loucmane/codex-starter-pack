# Task 134 Private GitHub Distribution and Cross-Machine Install Flow Tracker

**Started**: 2026-05-31
**Status**: ACTIVE
**Last Updated**: 2026-05-31

## Goals
- [x] Document and implement private GitHub install flow for Aegis
- [x] Verify Claude and Codex use the private repo distribution path across machines
- [x] Keep PyPI/TestPyPI out of scope and preserve existing project instructions

## Progress Log
- **2026-05-31 14:20** — [S:20260531|W:task134-private-github-distribution|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-05-31 14:20 CEST`
- **2026-05-31 14:20** — [S:20260531|W:task134-private-github-distribution|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/TRACKER.md] Scaffolded the Task 134 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-05-31 14:20** — [S:20260531|W:task134-private-github-distribution|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 134 in progress and updated only its generated task file
- **2026-05-31 14:20** — [S:20260531|W:task134-private-github-distribution|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 134 kickoff
- **2026-05-31 14:26** — [S:20260531|W:task134-private-github-distribution|H:apply_patch|E:docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/designs/private-github-install-flow.md] Re-scoped the generated kickoff plan to a private GitHub distribution mode with Claude/Codex registration and tmp-only acceptance evidence
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:apply_patch|E:aegis_foundation/mcp_registration.py] Implemented `private-github` source mode with `git+ssh://` default, SCP-style SSH remote normalization, and native Git auth safety metadata
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:pytest|E:cmd`env UV_CACHE_DIR=/tmp/uv-cache-task134 PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_invocation_contract.py -q`] Focused MCP registration and invocation-contract tests passed: 33 passed
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:command-generation|E:docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/command-generation-and-tests.md] Captured generated Claude and Codex private GitHub registration commands
- **2026-05-31 14:36** — [S:20260531|W:task134-private-github-distribution|H:pytest|E:cmd`env UV_CACHE_DIR=/tmp/uv-cache-task134 PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_schemas.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_invocation_contract.py -q`] Broader Aegis MCP/installer/schema/registration regression suite passed: 138 passed, 1 skipped
- **2026-05-31 14:38** — [S:20260531|W:task134-private-github-distribution|H:serena:memory|E:serena/memory:2026-05-31_task134_private_github_distribution_kickoff] Captured Task 134 continuity memory with implementation state, test evidence, and remaining private GitHub acceptance gap
- **2026-05-31 14:43** — [S:20260531|W:task134-private-github-distribution|H:private-github-smoke|E:docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/fresh-tmp-private-github-smoke.md] Fresh `/tmp` private GitHub smoke passed: private `uvx` source generated registration, described MCP config, initialized Codex runtime, started work, logged evidence, passed strict verify, closeout, and doctor
- **2026-05-31 14:45** — [S:20260531|W:task134-private-github-distribution|H:private-github-smoke|E:docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/reports/private-github-distribution/hpfetcher-copy-private-github-install.md] Copied HPFetcher private GitHub install smoke passed: real checkout remained untouched, copied CLAUDE.md content was preserved under the Aegis runtime block, AGENTS.md was created, expected Claude reload barrier appeared, and doctor was healthy
- **2026-05-31 14:47** — [S:20260531|W:task134-private-github-distribution|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 134 done and refreshed only `.taskmaster/tasks/task_134.md`

## Plan Compliance Checklist
- [x] plan-step-scope — Define private GitHub distribution contract and acceptance path
- [x] plan-step-implement — Update workflow/guard/docs and capture tests
- [x] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
