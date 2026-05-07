# Task 105 Validate and Harden Claude Runtime Adapter – Implementation Notes

## Planned Workstreams
- Audit current Claude Code hook surfaces against the completed Task 103 adapter.
- Harden hookable mutation gates where the audit finds a real behavior gap.
- Prove each enforcement claim with focused tests and stored evidence.

## Implementation Log
- 2026-05-07 — Hardened the Claude PreToolUse dispatcher to include MCP tools. Project settings now route `mcp__.*` tool names through `.claude/scripts/pretooluse-gate.sh`, and `gate_lib.py` classifies MCP calls as read-only, mutating, or unknown-persistent. Mutating and unknown MCP calls are blocked when readiness is `BLOCKED`; read-only MCP calls remain available for inspection.
- 2026-05-07 — Added protected-path checks for MCP tool payloads with common path fields such as `file_path`, `path`, and `relative_path`, preventing MCP tools from writing Codex-owned paths while readiness is `READY`.
- 2026-05-07 — Added `.claude/scripts/config-change-guard.sh` and registered it on `ConfigChange`. The guard blocks project `.claude/settings.json` changes from applying to the running Claude session if the required PreToolUse dispatcher or Stop handoff hook is missing or changed.
- 2026-05-07 — Updated `.claude/engine/runtime-contract.md` and `.claude/AGENTS.md` so future Claude sessions see Task 103 as implemented and Task 105 as hardening, with MCP and ConfigChange enforcement represented in the runtime contract.
- 2026-05-07 — Extended focused tests in `tests/claude_adapter/` for MCP read/write classification, protected-path MCP writes, ConfigChange hook protection, and stale runtime-contract references. Evidence: `reports/claude-runtime-adapter-hardening/tests-2026-05-07-claude-adapter.txt`.
