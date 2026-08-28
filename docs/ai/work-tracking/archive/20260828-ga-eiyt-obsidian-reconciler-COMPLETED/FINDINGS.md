# Findings

- 2026-08-28 — The prior manual-only projection was observably stale by a day and omitted current beads; a manual gate can detect staleness but cannot satisfy continuous-currentness or reboot expectations.
- 2026-08-28 — Atomic directory replacement requires write access to the output parent, not only the output directory. The hardened unit therefore derives an exact parent allowlist from the strict registry.
- 2026-08-28 — Source wrappers must bootstrap the repository root before importing local packages when invoked outside the checkout. The first live dry-run caught this pre-mutation and a RED external-CWD regression now covers it.
- 2026-08-28 — CI is evidence-heavy but over-coupled. P1 `ga-6w1y` records the merge-method contradiction and CI modernization scope; `ga-xk0m` records the narrower Taskmaster compatibility split.
- 2026-08-28 — Archive preconditions were satisfied and the completed bundle was preserved.
- 2026-08-28 — Active source readiness already supported Beads, but the completed-source fallback still required a numeric Taskmaster task. The supported archive therefore left a valid Beads bundle that the post-archive guard could not consume.
