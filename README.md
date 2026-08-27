# Aegis Foundation

Aegis Foundation is a portable multi-agent workflow foundation with runtime gates, Gas City bead-backed work authority, and an installer/MCP surface for adopting the system into other projects. Taskmaster remains a read-only compatibility surface for the historical backlog during migration.

The current release contract supports:

- bead-native CLI kickoff (`aegis kickoff --bead ...`) and MCP kickoff (`aegis.bead_kickoff`);
- passive S:W:H:E capture with mutation and closeout gates;
- a managed, one-way Obsidian projection gated at readiness, closeout, and publication boundaries;
- refusal of parallel local/Taskmaster allocation in beads-first repositories;
- development checkout invocation through `scripts/codex-task aegis ...`;
- editable package invocation through `aegis` and `aegis-mcp-server`;
- packaged asset resolution for the Aegis schemas, agent gates, helper scripts, and MCP diagnostics.

This is the Aegis 2.0 workflow foundation: beads own work, Git/CI own delivery truth, Aegis
owns passive evidence and gates, and Obsidian is a generated knowledge projection rather than a
second mutable ledger. See `docs/aegis/invocation-contract.md` and
`docs/aegis/beads-first-authority-and-obsidian-gate.md` for the operating contract.

For the read-only Codex Desktop + WSL + Gas City reboot doctor, stable user installation,
Windows logon-bootstrap contract, and attended reboot drill, see
`docs/operations/codex-wsl-reboot-readiness.md`.
