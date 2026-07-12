# Findings

- 2026-07-11 — The terminal source state is fully derivable, but moving an ACTIVE bundle also
  requires deterministic relocation of exact evidence references.



## Progress Log

- **2026-07-11 23:10** — [S:20260711|W:task244-derivable-source-closeout|H:docs/findings|E:docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/designs/source-closeout-derivation-contract.md] Confirmed the source lifecycle gap: readiness requires one ACTIVE tracker, while codex-guard can only fall back through installed current-work state; canonical and packaged readiness/guard assets are currently byte-identical.
- **2026-07-11 23:31** — [S:20260711|W:task244-derivable-source-closeout|H:docs/findings|E:docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/reports/derivable-source-closeout/task-verification.md] Live dogfood proved readiness derivation immediately and exposed stale plan evidence after the folder move; replay passed after the archive helper relocated exact references and refreshed hashes.
- **2026-07-12 02:11** — [S:20260712|W:task244-derivable-source-closeout|H:docs/findings|E:docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/reports/derivable-source-closeout/task-verification.md] Midnight publication exposed an ACTIVE-only continuation gap, now covered by completed-source session continuation; repeated xdist stdio timeouts were isolated to the smoke harness's text buffering.
