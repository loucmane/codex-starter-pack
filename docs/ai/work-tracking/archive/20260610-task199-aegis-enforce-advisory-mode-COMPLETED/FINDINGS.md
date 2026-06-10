# Findings

- 2026-06-10 — Advisory enforcement can be implemented without replacing the existing policy engine. The hook only needs a strict/advisory wrapper around existing block decisions, preserving strict behavior when `.aegis/state/enforcement.json` is absent.
- 2026-06-10 — `aegis enforce` must be a single-segment sanctioned mutation. Compound commands such as `aegis enforce --mode advisory && touch state.txt` remain blocked in strict mode.
- 2026-06-10 — Diagnostics need explicit mode surfacing. Doctor intentionally reports advisory as degraded/warning so operators cannot mistake record-only enforcement for strict protection.
