# Decisions

- 2026-05-08 — Implement Task 58 as a portable, non-mutating template versioning helper and policy layer rather than a bulk template migration engine.
- 2026-05-08 — Keep rollback support reviewable and non-destructive: generate rollback target data in history entries, but do not modify or restore template files automatically.
- 2026-05-08 — Keep migration support as compatibility assessment and guidance flags; executable migration tools remain out of scope until there is a separately scoped migration task.
- 2026-05-08 — Load versioning policy from the configured templates root so the helper stays portable across projects using the foundation.
