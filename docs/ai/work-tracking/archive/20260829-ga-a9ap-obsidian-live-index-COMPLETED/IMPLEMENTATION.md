# Bead ga-a9ap Refresh host Obsidian index after continuous Aegis publication – Implementation Notes

## Planned Workstreams
- Reproduce the stale open-host Obsidian index after an otherwise valid atomic managed-subtree publication.
- Add a strict optional registry contract and bounded host live-index adapter without changing filesystem authority.
- Refresh only after changed, fully gated publication; preserve no-op and host-unavailable behavior.
- Add explicit live-index readiness, packaging/schema coverage, focused regressions, and operator documentation.

## Progress Log

- **2026-08-29 02:02** — [S:20260829|W:ga-a9ap:red-green|H:docs/implementation|E:red:478cddb84ba3f0040b13724b702d9e86a3e79b7e;green:9a105c553810ca62ba52c75e99f71c6821284118;tree:0b268edcfff967959544fa7fb14c083851f1ed83] Added a strict registry-driven live-index adapter, changed-publication-only reload/read verification, bounded observer outcomes, explicit require-live-index checking, schema/runtime packaging, tests, and operator documentation.
