# Task 111 Aegis Cross-Project Smoke Kickoff

Date: 2026-05-17
Branch: `feat/task-111-aegis-cross-project-smoke`

Context:
- Taskmaster Task 111 was created after all previous 110 tasks were done.
- Title: Aegis Cross-Project Install Smoke Harness and Distribution Readiness.
- Dependencies: Task 101 and Task 110.
- Task 111 is in progress and expanded into five subtasks: scope matrix, CLI smoke coverage, MCP wrapper equivalence coverage, safety/negative cases, and evidence/closeout.
- Session: `sessions/2026/05/2026-05-17-002-task111-aegis-cross-project-smoke.md`.
- Plan: `plans/2026-05-17-task111-aegis-cross-project-smoke.md`.
- Active work tracking: `docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/`.
- Scope design: `designs/aegis-cross-project-smoke-matrix.md`.

Important notes:
- The first `task-master add-task` attempt used shell backticks in the prompt and zsh interpreted them; it failed without file changes. The successful retry used safe quoting and an approved outside-sandbox Taskmaster provider call.
- The kickoff wizard generated generic wizard-flow plan wording; this was corrected before implementation.
- Task 111 must preserve the Task 48/109/110 architecture: `scripts/_aegis_installer.py` is source of truth, `scripts/codex-task aegis ...` is the CLI wrapper, and `aegis_mcp/server.py` is the MCP wrapper/control plane.
- The smoke harness must use isolated temp target repos and must not treat the source repository as an Aegis install target.

Next implementation step:
- Start subtask 111.2 by adding `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py` with CLI smoke coverage for empty, Python/library, web/app, docs-heavy, and partial Aegis target shapes.
