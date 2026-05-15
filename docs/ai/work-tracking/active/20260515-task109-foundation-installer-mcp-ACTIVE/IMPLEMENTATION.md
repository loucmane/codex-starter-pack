# Task 109 Portable Foundation Installer and MCP Distribution Contract – Implementation Notes

## Planned Workstreams
- 109.1 - Architecture decision and distribution contract: completed in `designs/foundation-installer-mcp-architecture.md`.
- 109.2 - Manifest, profile, and install-plan schema: pending.
- 109.3 - Generic-profile CLI installer lifecycle and verification commands: pending.
- 109.4 - Fixture, idempotence, and V1 rollback/cleanup tests: pending.
- 109.5 - MCP wrapper contract, deferred follow-up tasks, evidence, and handoff: pending.

## Current Implementation Boundary
- The deterministic CLI/library core is the source of truth.
- The MCP server is an optional wrapper over the same library.
- The first implementation should avoid duplicating installer logic between CLI and MCP.
- Mutating installer/update/rollback operations must produce rollback checkpoints and verification evidence.
- V1 is limited to contract/schema plus a generic-profile CLI prototype. Full MCP server, full multi-profile support, complex update migrations, package publishing, and automatic CI installation are deferred.
- Taskmaster AI-backed parent updates are viable with `codex-cli`/`gpt-5.5` and PATH `codex`, but they remain slow/heavy and can emit drift warnings. Use them only for narrow parent scope updates, then run targeted `generate-one`, inspect diffs, and verify Taskmaster health.
- Taskmaster is currently configured for `codex-cli`/`gpt-5.5` with `codexCli.reasoningEffort=medium` and `codexCli.codexPath` pointing to the PATH-resolved global Codex CLI 0.130.0 executable. The explicit codexPath override is required because Taskmaster's bundled `@openai/codex` 0.60.1 is too old for `gpt-5.5`.
