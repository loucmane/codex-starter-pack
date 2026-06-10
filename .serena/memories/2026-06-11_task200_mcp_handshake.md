# 2026-06-11 Task 200 MCP version handshake

Implemented in aegis_mcp/server.py: startup runtime_fingerprint (sha256 of installer/
gate_lib/ledger_lib + source commit) rechecked in run_tool on every call; stale →
mutations refused (runtime_stale_reload_required) before action decisions, reads warn
via runtime_stale block; runtime_status exposes both fingerprints. 5 tests incl. the
HP-Coach empty-repair-plan repro.
