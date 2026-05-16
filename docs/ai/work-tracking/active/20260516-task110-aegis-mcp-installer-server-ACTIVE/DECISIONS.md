# Decisions

- 2026-05-16 — Task 110 will implement a production MCP server as a thin wrapper over `scripts/_aegis_installer.py`. The server must not duplicate installer logic, must not expose deferred mutating tools as active production tools, and must keep prompts advisory rather than treating them as evidence or gates.
