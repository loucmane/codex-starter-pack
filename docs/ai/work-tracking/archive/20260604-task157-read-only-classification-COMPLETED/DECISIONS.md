# Decisions

- 2026-06-04 — Keep the Bash classifier conservative and do not generally allow jq or shell pipelines; expose only structurally read-only Aegis projections.
- 2026-06-04 — Confine Aegis target selection before read-only short-circuit so out-of-root reads fail even when readiness is blocked.
- 2026-06-04 — Treat ambiguous pending/log events neutrally; do not infer `plan-step-implement` from free-text handler/evidence substrings.
- 2026-06-04 — Return structured MCP `invalid_target` errors instead of silently falling through to installer errors for out-of-root tool targets.
