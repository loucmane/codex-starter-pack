# TM #200 scope — MCP/CLI version handshake

Task text: prevent stale MCP logic after source-root updates; MCP exposes its source
commit/capabilities, compares against the active source root, returns
reload_required/degraded when stale; acceptance reproduces the HP-Coach empty-repair-
plan case and proves the mismatch is detected before action decisions.

## Implemented design
- runtime_fingerprint(source_root): sha256 of the runtime-bearing files
  (_aegis_installer.py, gate_lib.py, ledger_lib.py) + best-effort source commit.
- create_server captures the startup fingerprint; run_tool (the single dispatch
  wrapper) recomputes on EVERY call: mutating tools are REFUSED with
  runtime_stale_reload_required (blocked) when fingerprints diverge — before any
  action decision; read-only tools still answer but carry a runtime_stale warning
  block with both fingerprints and restart guidance.
- aegis.runtime_status result gains mcp_server {started_fingerprint,
  on_disk_fingerprint, stale} for diagnosis.
- Degraded-not-dead: a stale server stays useful for reads (matching the original
  design intent: refuse mutations, keep serving reads).
