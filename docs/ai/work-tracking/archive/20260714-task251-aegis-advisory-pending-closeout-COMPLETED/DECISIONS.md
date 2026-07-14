# Decisions

- 2026-07-14 — Classify pending state once from stored provenance and share that result across status, verify, closeout, closeout readiness, doctor, next guidance, and repair guidance.
- 2026-07-14 — Advisory-only residue is preserved audit evidence, not a cleanup backlog; it remains non-blocking even after strict re-entry. Explicit strict/required, mixed, malformed, or unknown state fails closed.
- 2026-07-14 — Keep complete events only in the canonical queue artifact and expose exact counts plus bounded samples in reports and agent-facing output.
- 2026-07-14 — Do not touch Blog during upstream implementation. Gas Town migration remains deferred until explicit owner authorization at a sensible stopping point.
- 2026-07-14 — Retain the compatibility gate ID `mutation.pending_tracking_empty`; its structured result now expresses delivery safety instead of requiring literal absence for advisory-only evidence.
- 2026-07-14 — Treat missing/unknown mode, invalid event shape, invalid JSON, non-object payloads, and non-list queues as untrusted. Aegis may point to read-only diagnosis but must not invent a repair or silently discard evidence.
- 2026-07-14 — Keep the location-sensitive reconcile test unchanged because Task 251 does not alter reconcile behavior; record the `/tmp` worktree limitation and rely on the non-temp targeted proof plus protected CI checkout.
