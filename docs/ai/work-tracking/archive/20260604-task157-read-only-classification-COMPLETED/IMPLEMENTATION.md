# Task 157 Harden read-only access and tracking classification – Implementation Notes

## Planned Workstreams
- Confined Aegis `target_dir` handling in `.claude/scripts/gate_lib.py` and the packaged hook asset so read-only Aegis CLI/MCP calls cannot inspect outside the governed project root before readiness.
- Reused the main Bash/MCP read-only classifier from degraded fallback instead of maintaining a separate permissive allowlist.
- Added MCP-server-side target confinement in `aegis_mcp/server.py`, returning structured `invalid_target` errors for out-of-root targets.
- Hardened reconcile `base_ref` validation in `scripts/_aegis_installer.py` to reject option-shaped or whitespace/NUL-containing values before invoking git.
- Removed substring-based implementation inference from log event/plan-step inference; only explicit event classes or confident file mutation pending events infer implementation.
- Added focused tests for target confinement, degraded/main classifier parity, generic jq refusal, read-only no-pending behavior, MCP invalid-target responses, option-shaped `base_ref`, and neutral ambiguous logging.
