# Decisions

- 2026-05-10 — Do not re-extract or rewrite existing critical handler bodies. Current evidence shows the modular handler files already exist; Task 26 will fix registry/discovery compatibility instead.
- 2026-05-10 — Add `templates/handlers/index.md` as the concrete modular handler-family landing page and redirect `templates/HANDLERS.md` compatibility lookup to that index instead of a bare directory.
- 2026-05-10 — Teach `TemplateRegistry` to resolve modular records by frontmatter `id` and explicit aliases. This preserves path-derived registry IDs while making human-facing handler names load correctly.
- 2026-05-10 — Treat `fix-problem` and `test-implementation` as legacy aliases, not new canonical handler files. `fix-problem` maps to `fix-bug`; `test-implementation` maps to `create-test-checkpoint` for the critical handler migration compatibility path.
