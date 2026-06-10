# Task 200 Aegis MCP CLI version handshake – Implementation Notes

- runtime_fingerprint(): sha256 over _aegis_installer.py / gate_lib.py / ledger_lib.py
  at the active source root + best-effort source commit.
- create_server() captures the startup fingerprint; run_tool() rechecks per call:
  mutating tools refused with runtime_stale_reload_required (blocked, both fingerprints
  + restart guidance in details) BEFORE any action decision; read-only tools answer
  with a runtime_stale warning attached. aegis.runtime_status exposes
  mcp_server.{started,on_disk,stale}.
- 5 tests incl. the HP-Coach acceptance repro: a stale server refuses aegis.repair
  before producing any (stale/empty) plan; kickoff refused; reads warn; fresh server
  clean. Full suite green (see reports/).
