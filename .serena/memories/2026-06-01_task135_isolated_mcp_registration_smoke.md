# Task 135 Isolated Native MCP Registration Smoke

Implemented a new Aegis native MCP smoke command that registers and verifies Claude/Codex MCP entries inside isolated temporary client homes/config roots.

Key changes:
- `aegis_foundation/mcp_registration.py` adds `smoke_registration`, isolated env helpers, optional report writers, env-aware `run_native_client`, and `SMOKE_CLIENTS=("claude", "codex")`.
- `aegis_foundation/cli.py` adds `aegis mcp smoke-registration` with repeatable `--client`, source-selection flags, `--smoke-root`, `--keep-temp`, JSON report, and Markdown report options.
- `scripts/codex-task` mirrors the package CLI command; packaged script/docs assets are synced.
- Docs updated in `docs/aegis/mcp-client-setup.md` and `docs/aegis/release-verification-matrix.md` to make isolated smoke the release-safe native client proof.

Verification so far:
- Focused native registration/release distribution tests: 45 passed, 2 expected wheel-smoke skips.
- Broader Aegis contract subset: 158 passed, 3 expected smoke-gated skips.
- Real native smoke against private GitHub tag `aegis-private-github-20260531`: passed for both Claude and Codex with temp homes and temp `CODEX_HOME`; reports stored under Task 135 work-tracking reports.

Operational note:
- Task 134 active folder was archived to satisfy guard invariant of one active folder. Task 135 is active on branch `feat/task-135-isolated-mcp-registration-smoke`.