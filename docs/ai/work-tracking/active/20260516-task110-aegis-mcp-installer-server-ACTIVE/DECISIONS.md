# Decisions

- 2026-05-16 — Task 110 will implement a production MCP server as a thin wrapper over `scripts/_aegis_installer.py`. The server must not duplicate installer logic, must not expose deferred mutating tools as active production tools, and must keep prompts advisory rather than treating them as evidence or gates.
- 2026-05-16 — Subtask 110.2 registers public tool schemas but returns `handler_deferred` for valid calls. Core installer execution stays in 110.3 so the public MCP contract can be tested independently from mutation wiring.
- 2026-05-16 — MCP tool success responses use an `{ok:true,result:...}` wrapper and predictable failures use `{ok:false,error:{code,message,status,details}}`. This gives clients a stable envelope while preserving the original core installer report under `result` or `error.details.report`.
