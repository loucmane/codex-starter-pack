# Findings

- 2026-08-28 — Claude's readiness policy was duplicated inside a 963-line shell-embedded Python program; every adapter fix therefore risked semantic divergence from Aegis.
- 2026-08-28 — `.claude/scripts/gate_lib.py` had accumulated 4,319 lines spanning contracts, policy, state, evidence, tracking, and lifecycle. Its breadth, rather than the amount of policy, was the maintainability defect.
- 2026-08-28 — Installed projects already carry an Aegis runtime pointer and project-local CLI. That is the durable upgrade seam; copying another monolithic implementation into each project would perpetuate drift.
- 2026-08-28 — The existing hook contract can remain stable while implementation ownership moves into importable modules. Thin launchers preserve rollback and older integrations without remaining policy authorities.
- 2026-08-28 — Cross-project testing proved a source-pointer-only modular runtime was insufficient: hooks must survive an unavailable source checkout. The durable boundary is a narrow manifest-bound gate snapshot in each target, not another copied monolith or a global environment assumption.
- 2026-08-28 — Hosted CI exposed stale managed-update golden counts and operation digests after the manifest-managed target-local runtime added 21 intentional assets. The installer behavior was correct; the frozen Codex, HPFetcher, and Blog plan fixtures had not been regenerated. Re-derived all three values from the final plan operations while preserving their exact non-skip classifications.
- 2026-08-28 — Archive preconditions were satisfied and the completed bundle was preserved.
