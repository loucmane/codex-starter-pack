# Decisions

- 2026-08-28 — Beads remain the primary work authority. Taskmaster is compatibility-only and is consulted only where a target project explicitly requires it.
- 2026-08-28 — `aegis gate readiness` is the canonical readiness API. `.claude/scripts/readiness.sh` remains temporarily as a thin compatibility launcher and contains no policy.
- 2026-08-28 — Claude hook policy lives in `aegis_foundation.gate.hooks`, divided by responsibility. `.claude/scripts/gate_lib.py` is a fail-closed adapter launcher only.
- 2026-08-28 — Individual policy modules have a 700-line ceiling and launchers an 80-nonblank-line ceiling, both enforced by tests.
- 2026-08-28 — Release certification must prove the canonical readiness and hook modules are present in both wheels and source distributions.
- 2026-08-28 — Managed projects receive a checksummed `.aegis/runtime/python` gate snapshot. Hooks prefer it over the source pointer, so reboot, mount, checkout, or source-update failures cannot silently remove authorization policy.
