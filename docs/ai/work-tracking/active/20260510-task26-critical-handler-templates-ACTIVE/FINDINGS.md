# Findings

- 2026-05-10 — The historical Task 26 wording is stale: critical handler content is already modular under `templates/handlers/**`, and handler frontmatter is already governed by `templates/metadata/template-metadata-policy.json`.
- 2026-05-10 — `TemplateRegistry.resolve("templates/HANDLERS.md", allow_serena=False)` redirects to `templates/handlers/` with `record=None`, so the handler family lacks the concrete modular index behavior already added for patterns in Task 27.
- 2026-05-10 — Critical handler IDs do not resolve directly through `TemplateRegistry`: `start-new-work`, `fix-bug`, and `create-test-checkpoint` miss because registry index IDs are path-derived and the loader does not alias frontmatter `id` values.
- 2026-05-10 — Legacy names from the old migration wording remain unresolved: `fix-problem` suggests `handlers-triggers-debug-fix-bug`, and `test-implementation` suggests current testing handlers, but neither loads directly.
- 2026-05-10 — `templates/matrices/mapping/keyword-to-handler.md` still routes keyword `problem` to nonexistent `fix-problem`; it should route to the canonical `fix-bug` handler while preserving `fix-problem` as an alias.
