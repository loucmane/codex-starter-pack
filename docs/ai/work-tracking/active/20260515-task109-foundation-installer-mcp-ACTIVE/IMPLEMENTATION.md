# Task 109 Portable Foundation Installer and MCP Distribution Contract – Implementation Notes

## Planned Workstreams
- 109.1 - Architecture decision and distribution contract: completed in `designs/foundation-installer-mcp-architecture.md`.
- 109.2 - Manifest, profile, and install-plan schema: pending.
- 109.3 - CLI installer lifecycle and verification commands: pending.
- 109.4 - Fixture, idempotence, rollback, and cross-agent tests: pending.
- 109.5 - MCP wrapper contract, resources, prompts, evidence, and handoff: pending.

## Current Implementation Boundary
- The deterministic CLI/library core is the source of truth.
- The MCP server is an optional wrapper over the same library.
- The first implementation should avoid duplicating installer logic between CLI and MCP.
- Mutating installer/update/rollback operations must produce rollback checkpoints and verification evidence.
