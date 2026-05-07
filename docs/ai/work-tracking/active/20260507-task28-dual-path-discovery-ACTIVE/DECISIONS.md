# Decisions

- 2026-05-07 — Treat Task 28 as an extension of the existing `TemplateRegistry.resolve()` API rather than a new discovery subsystem. This preserves Task 8/13 behavior and aligns with the portable-foundation rule that core logic should be config-driven and shared across projects.
- 2026-05-07 — Keep Serena as a structured operator fallback action. Task 28 will not introduce a live in-process Serena dependency or background semantic index because that would make the portable registry depend on an optional MCP service.
- 2026-05-07 — Interpret "metrics", "cache warming", and "discovery hints" as in-memory registry observability and deterministic local suggestions. Persistent telemetry, dashboards, and external service monitoring remain out of scope for this task.
