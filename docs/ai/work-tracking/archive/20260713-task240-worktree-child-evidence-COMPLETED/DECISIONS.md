# Decisions

- 2026-07-13 — Keep ledger schema version `1` and ship nullable additive fields plus SQLite read/write migration; do not rewrite historical rows.
- 2026-07-13 — Derive repository/worktree/branch/HEAD once per ledger open, while explicit event or adapter-bridge identity always wins.
- 2026-07-13 — Merge passive Codex lifecycle hooks through the installer and invoke the installed Aegis shim; do not copy mutable ledger state or vendor a second recorder into each worktree.
- 2026-07-13 — Treat missing client-provided child identity as an explicit capability gap. Never relabel parent traffic as child implementation evidence.
- 2026-07-13 — Install synchronous Codex recorder hooks because the current client skips async command handlers; bound them to passive, exception-swallowing commands and require exact-hash trust before clearing the Codex reload marker.
- 2026-07-13 — Merge and uninstall `.codex/hooks.json` structurally by exact Aegis-owned command identity. Preserve unrelated project hooks and refuse malformed JSON instead of replacing it.
- 2026-07-13 — Propagate child identity into automatically derived scope rows so projections do not lose provenance at the first-mutation boundary.
- 2026-07-13 — Use ledger `seq`, not random event IDs, when lifecycle order is semantically relevant.
- 2026-07-13 — Do not install or fabricate Aegis mutable workflow state in the source worktree solely to make installed-target verification green. Use the established source-repository lifecycle and require hosted witness/CI before completion.
- 2026-07-13 — Keep the temp-path reconcile test unchanged and disclose the local environment mismatch; do not weaken its governed-repository safety assertion to obtain a cosmetic all-green local run.
- 2026-07-14 — Compose Task 240's worktree/child evidence with current-main Codex adapter behavior in one normal merge commit; do not rebase, force-push, fabricate installed source-worktree state, or rewrite historical Task 247-251 evidence.
- 2026-07-14 — Treat fresh exact-head hosted CI as the authoritative resolution for merge-context guard noise after local Task 240 evidence and compatibility tests pass.
- 2026-07-14 — Make guard provenance merge-aware instead of bypassing hooks or rewriting history: exclude only clean staged paths absent from the index-to-MERGE_HEAD diff, retain every other status entry, and return the unfiltered set if Git inspection fails.
