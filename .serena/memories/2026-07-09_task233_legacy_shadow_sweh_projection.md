# Task 233: Legacy-shadow S:W:H:E projection

- Implemented deterministic projection from the passive Aegis ledger into existing session, plan, tracker, findings, implementation, changelog, decisions, and handoff surfaces.
- Generated blocks are marker-bounded, preserve human content, and are idempotent.
- Added `aegis ledger project-sweh` and opt-in `aegis scope set --project-sweh`.
- Added agent-scoped client-reload handling so a Claude-only reload marker does not block a positively identified Codex invocation; unknown and matching Claude callers remain blocked.
- Added read-only SQLite/JSONL ledger access, including sandbox fallback for SQLite immutable snapshots.
- Dogfooded against HP-Fetcher evidence and `/home/loucmane/dev/blog`; the blog run projected two scope events into eight surfaces, survived archival, and closed with zero unexpected changes.
- Validation: 156 affected tests passed with one opt-in certification smoke skipped; final observation and packaged-mirror checks also passed. Taskmaster health and dependency validation were clean.
- TM-210 now depends on TM-233. PR-4 remains blocked pending witness/delivery projection, explicit MCP caller identity, multiple real task runs, and unique-content parity evidence.
- Publication branch: `feat/task-233-legacy-shadow-sweh-projection`.