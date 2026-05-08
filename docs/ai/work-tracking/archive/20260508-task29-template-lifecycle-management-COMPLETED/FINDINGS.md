# Findings

- 2026-05-08 — Existing metadata work already provides `title`, `type`, `status`, schema-backed frontmatter validation, and registry discovery; Task 29 should build on those surfaces rather than replacing them.
- 2026-05-08 — The current frontmatter schema does not include the historical Task 29 `review` or `archived` lifecycle states, while existing repository metadata still uses compatibility states such as `beta` and `experimental`.
- 2026-05-08 — The repo has a real deprecated template tombstone, `templates/behaviors/session/compaction-detection.md`, but no machine-readable deprecation date, replacement/migration notice contract, grace-period audit, or archival-readiness check.
- 2026-05-08 — `templates/registry/index.md` uses `status: modular` as an aggregate registry marker; it should be ignored by lifecycle audits rather than mapped to a real template lifecycle state.
- 2026-05-08 — Final lifecycle audit reports `221 records, 0 issue(s)`, so the policy can land without forcing a bulk template migration.
