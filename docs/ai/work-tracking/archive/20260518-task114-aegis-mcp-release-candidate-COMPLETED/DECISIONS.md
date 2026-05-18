# Decisions

- 2026-05-18 — Validate local wheel/sdist artifacts as the Task 114 release-candidate baseline. Treat GitHub release artifacts as the likely first public distribution channel if evidence is green, and defer PyPI publication to a later explicit task.
- 2026-05-18 — Release readiness recommendation is go for GitHub release-candidate artifact preparation, but no-go for direct PyPI publication in this task. PyPI requires a separate release task with checksums/provenance and downstream install verification.
