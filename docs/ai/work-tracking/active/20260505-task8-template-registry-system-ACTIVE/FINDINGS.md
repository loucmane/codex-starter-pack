# Findings

- 2026-05-05 - `templates/registry/index.json` is a static discovery surface with 99 entries and minimal fields (`id`, `path`, `tags`, `goodFirstHandler` or `goodFirstWorkflow`); it is not a runtime registry API.
- 2026-05-05 - `templates/metadata/template-summary.csv`, `template-inventory.txt`, and `template-overview.md` provide generated metadata surfaces, but callers still need to parse/search them manually.
- 2026-05-05 - `scripts/codex-guard` and `scripts/template-ssot-scanner/scanner.py` contain useful metadata parsing logic, but neither exposes a portable `TemplateRegistry` abstraction.
- 2026-05-05 - The portable foundation requires new registry code to derive paths from `scripts/_repo_structure.py` so it works across repo shapes instead of hardcoding `templates/`.
- 2026-05-05 - The implementation can satisfy Task 8 without replacing static registry/metadata files by adding a reusable registry module over the existing surfaces.
