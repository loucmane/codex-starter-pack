# Bead ga-ur1c.3 Continuously reconcile every registered project into Obsidian – Changelog

- 2026-08-31 — Attached repair bead `ga-ve57`: bind generated exports to explicit host rig roots,
  use a bounded 30-second live-index read, and restore reconciler state/output/unit status exactly
  after a failed live apply.
- 2026-08-31 — Extended the installer control-plane deadline to cover a complete four-project
  cycle, made timer activation/repetition restart-safe, and added exact timer-substate rollback
  verification with byte-exact post-prime state/output restoration.
- 2026-08-31 — Raised the still-bounded agent projection ceiling to 5,000, batched live-index
  observation behind one reload per shared endpoint, and made rollback wait through persistent
  timer catch-up before its final exact restore.
- 2026-08-31 — Ordered project live-index observation before continuity-dashboard capture so the
  dashboard and its immediate check share one state; moved rollback `reset-failed` after the
  restored timer/service reload and added exact final service-state verification.
- 2026-08-31 — Merged and installed v0.6.4, published all four registered project projections
  plus Continuity, and proved host live-index freshness, a byte-identical no-reload cycle, an
  unchanged WSL Obsidian process epoch, a healthy persistent timer, and suspended project rigs.

- 2026-08-31 15:17 CEST — Initialized active work-tracking folder.
- 2026-08-31 17:23 CEST — Archived active work-tracking folder.
