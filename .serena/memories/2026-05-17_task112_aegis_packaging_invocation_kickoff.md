# Task 112 - Aegis Packaging and Invocation Contract Kickoff

Date: 2026-05-17
Branch: feat/task-112-aegis-packaging-invocation-contract
Session: sessions/2026/05/2026-05-17-003-task112-aegis-packaging-invocation-contract.md
Plan: plans/2026-05-17-task112-aegis-packaging-invocation-contract.md
Work tracking: docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/

Taskmaster state:
- Parent Task 112 created and set in-progress.
- Dependencies: 109, 110, 111 all complete.
- Subtasks created: 112.1 scope, 112.2 external-cwd local checkout, 112.3 package-style CLI/module invocation, 112.4 external MCP startup/config snippets, 112.5 final evidence/handoff.
- 112.1 is scoped as completed once the design/plan/tracker updates are synced.

Scope decision:
- V1 contract supports a development/local-checkout form using absolute paths from an external project cwd.
- V1 also targets a package-style local invocation path, preferring console scripts (`aegis`, `aegis-mcp-server`) if narrow packaging changes are enough; fallback is a tested `python -m ...` entrypoint.
- MCP contract should preserve `AegisMCPConfig.from_paths`, `--source-root`, `--default-target-dir`, `AEGIS_SOURCE_ROOT`, and `AEGIS_DEFAULT_TARGET_DIR`.

Boundaries:
- Keep installer semantics in `scripts/_aegis_installer.py`.
- Keep `scripts/codex-task aegis ...` as the repository-local wrapper.
- Keep `aegis_mcp/server.py` as the MCP control plane.
- Do not publish Aegis publicly, implement rollback/update migrations, signing, hosted services, CI install templates, or a second installer engine in Task 112.

Next work:
1. Implement 112.2 with external-cwd tests and `docs/aegis/invocation-contract.md`.
2. Implement 112.3 with the selected package-style invocation surface.
3. Implement 112.4 MCP external startup/config tests and docs.
4. Finish 112.5 evidence, Taskmaster refresh, guard/audit/diff-check, and release-hardening follow-up recommendation.