# Task 134 Private GitHub Distribution Kickoff

- Branch: `feat/task-134-private-github-distribution`
- Taskmaster Task 134 is `in-progress`.
- Work context: `task134-private-github-distribution`.
- Active folder: `docs/ai/work-tracking/active/20260531-task134-private-github-distribution-ACTIVE/`.
- Plan: `plans/2026-05-31-task134-private-github-distribution.md`.
- Session: `sessions/2026/05/2026-05-31-004-task134-private-github-distribution.md`.
- Implemented first pass: `private-github` MCP registration source mode in `aegis_foundation/mcp_registration.py`, CLI/wrapper choices in `aegis_foundation/cli.py` and `scripts/codex-task`, docs in `docs/aegis/{mcp-client-setup,distribution,invocation-contract}.md`, and tests in `tests/meta_workflow_guard/{test_aegis_native_mcp_registration.py,test_aegis_invocation_contract.py}`.
- Generated private commands for Claude/Codex use `uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@main` and record safety note `private-github-requires-native-git-auth`.
- Test evidence so far: focused registration/invocation tests passed `33 passed`; broader Aegis MCP/installer/schema/registration suite passed `138 passed, 1 skipped` using `UV_CACHE_DIR=/tmp/uv-cache-task134` because sandboxed `~/.cache/uv` is read-only.
- Stale Task 133 active work-tracking folder was archived to `docs/ai/work-tracking/archive/20260531-task133-codex-live-aegis-acceptance-COMPLETED/` so the active-folder guard can focus on Task 134.
- Next acceptance gap: true private GitHub `uvx` smoke needs this branch available on GitHub, then run from `/tmp` against `git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution` or a pinned commit/tag. Do not mutate real HPFetcher; only tmp copies.