# Decisions

- 2026-08-29 — Reuse the already-proven reboot transition and current reboot-persistence checks instead of restarting WSL or Windows again. A new reboot would add disruption without testing a different contract.
- 2026-08-29 — Keep lifecycle ownership split: `ga-vqm2` coordinates recovery certification, `ga-0szv` owns future-project onboarding/bundle proof, `ga-bzn3` owns watch-officer delivery, and `blog-6r1b` records the Blog-specific worker permission defect. Close each only on its own acceptance evidence.
- 2026-08-29 — Fix Blog access at the declarative profile source and generated live configuration; do not widen the signer, add wildcard roots, or grant the worker the Blog checkout itself.
- 2026-08-29 — Use only the installed fixed broker operation for the managed-signing bundle proof. No bespoke root script or ad-hoc copy is permitted.
- 2026-08-29 — Treat the session ledger and host tmux scan as independent evidence. A known childless, sessionless `tmux -L city` server is recovered only by one identity-pinned graceful `kill-server`; any child, hosted session, identity drift, or unknown server is a stop.
- 2026-08-29 — Codify retry by mutation state rather than attempt count: safe non-live/pre-mutation retries are append-forward; fully rolled-back live retries require a proven cause correction; ambiguous partial live state is never retried.
- 2026-08-29 — Keep deterministic filesystem projection authoritative and require live Obsidian IPC only as a separate host-observer acceptance fact. Managed vault bytes are never hand-edited.
- 2026-08-29 — Archived through the supported archive helper; no evidence was deleted.
