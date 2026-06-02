# Decisions

- 2026-06-02 — Use a positive approved-context proof allowlist instead of trying to detect agents. Absence of proof, malformed proof, unknown context type, or task/proof mismatch all refuse by default.
- 2026-06-02 — Keep the current enable gate intentionally unsatisfiable. Even future-shaped approved contexts and enable-shaped kill-switch state return `enabled=false` until a later task deliberately enables a bounded apply path.
- 2026-06-02 — Model apply audit records now, but do not write them. The record builder validates proof binding, idempotency key, previous hash, external anchor, rollback handle, and before/after delta hashes without creating any persistent transaction log.
- 2026-06-02 — Treat kill-switch state as fail-safe and asymmetric: missing, corrupt, unreadable, malformed, or explicitly disabled state all disable apply; explicit disable wins over any enable-shaped state.
- 2026-06-02 — Do not expose an apply scaffold through the CLI, MCP, or Codex helper. Tests must prove the scaffold is unreachable from agent-facing surfaces.
