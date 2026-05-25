# Task 123 Aegis Release Candidate Global MCP Kickoff

Task 123 is active on `feat/task-123-aegis-release-candidate-global-mcp-install-proof`.

Scope:
- build or expose a local Aegis release-candidate artifact,
- prove Aegis MCP starts from outside `/home/loucmane/codex`,
- install Aegis into a copied existing project supplied by the user,
- use Aegis MCP as the workflow control plane and native tools for source edits,
- prove readiness, pending S:W:H:E tracking, strict verification, `closeout_ready`, and closeout,
- document install, uninstall, rollback, publication decision, and limitations before any TestPyPI/PyPI step.

Primary acceptance target is a `/tmp` copy of an existing project. The original project must not be mutated.

