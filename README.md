# Aegis Foundation

Aegis Foundation is a portable multi-agent workflow foundation with runtime gates, Gas City bead-backed work authority, and an installer/MCP surface for adopting the system into other projects. Taskmaster remains a read-only compatibility surface for the historical backlog during migration.

The current release contract supports:

- development checkout invocation through `scripts/codex-task aegis ...`;
- editable package invocation through `aegis` and `aegis-mcp-server`;
- packaged asset resolution for the Aegis schemas, agent gates, helper scripts, and MCP diagnostics.

See `docs/aegis/invocation-contract.md` for the command contract and current release-hardening status.

For the read-only Codex Desktop + WSL + Gas City reboot doctor, stable user installation,
Windows logon-bootstrap contract, and attended reboot drill, see
`docs/operations/codex-wsl-reboot-readiness.md`.
