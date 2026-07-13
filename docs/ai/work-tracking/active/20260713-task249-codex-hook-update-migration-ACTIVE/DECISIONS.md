# Decisions

- 2026-07-13 — Reorder project-update apply rather than weakening schema validation.
  The reviewed installer migration writes a current-schema manifest first; the existing
  strict `runtime_update` then refreshes source metadata and the pointer.
- 2026-07-13 — Keep direct runtime updates strict. A legacy manifest that fails the current
  schema cannot be advanced independently of the managed installer migration.
- 2026-07-13 — Preserve divergent `.codex/hooks.json` as operator-owned manual review.
  Task 249 does not add overwrite, force-adoption, or hook-trust bypass behavior.
- 2026-07-13 — Treat the Blog checkout as read-only while Task 40 is active. Reproduce and
  verify only in a disposable snapshot until Blog reaches a safe checkpoint.
