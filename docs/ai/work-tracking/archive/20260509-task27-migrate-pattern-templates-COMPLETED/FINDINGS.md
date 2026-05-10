# Findings

- 2026-05-09 — Task 27 historical scope is mostly stale: `templates/PATTERNS.md` is already a modular legacy entrypoint, and `templates/patterns/` already contains the work-tracking/session/evidence/routing/selection/integration pattern modules.
- 2026-05-09 — `TemplateRegistry.resolve("templates/PATTERNS.md")` redirected to `templates/patterns/` with `record=None`, which means compatibility lookup had a target but no concrete modular record.
- 2026-05-09 — Pattern modules already contain canonical frontmatter, but `templates/metadata/template-metadata-policy.json` did not govern `templates/patterns/**/*.md`, leaving pattern metadata outside guard enforcement.
- 2026-05-09 — Taskmaster status writes are not safe to parallelize: running two `task-master set-status` commands concurrently caused the 27.1 completion write not to persist. Serial rerun corrected it.
