# Task 135 Add Isolated Native MCP Registration Smoke Command for Aegis – Implementation Notes

## Planned Workstreams
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:scope|E:aegis_foundation/mcp_registration.py] Add isolated native MCP registration smoke helper while preserving existing register/generate/execute/verify contracts.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:scope|E:aegis_foundation/cli.py] Expose `aegis mcp smoke-registration` for package installs.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:scope|E:scripts/codex-task] Mirror the smoke command in the repo-local wrapper.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:implementation|E:aegis_foundation/mcp_registration.py] Implemented environment-aware native client execution plus `smoke_registration()` to create per-client temp homes, pre-create Codex `CODEX_HOME`, run register+verify, and return aggregate structured status.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:implementation|E:aegis_foundation/cli.py] Added `aegis mcp smoke-registration` with repeatable `--client`, source-selection flags, `--smoke-root`, `--keep-temp`, `--report-file`, and `--markdown-report-file`.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:implementation|E:scripts/codex-task] Mirrored the package CLI command in the repository helper and synced `aegis_foundation/assets/scripts/codex-task`.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:verification|E:docs/ai/work-tracking/active/20260601-task135-isolated-mcp-registration-smoke-ACTIVE/reports/isolated-mcp-registration-smoke/native-smoke.json] Verified real Claude and Codex native registration in isolated temp homes against private GitHub tag `aegis-private-github-20260531`.
- [S:20260601|W:task135-isolated-mcp-registration-smoke|H:verification|E:tests/meta_workflow_guard/test_aegis_native_mcp_registration.py] Verified fake-client, missing-client, package CLI, repo wrapper, report writer, and release matrix behavior through focused and broader pytest runs.
