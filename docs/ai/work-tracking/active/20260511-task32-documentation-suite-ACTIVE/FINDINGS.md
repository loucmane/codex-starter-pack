# Findings

- 2026-05-11 — User-facing documentation entrypoints lag behind the current foundation. `templates/USER-GUIDE.md` and `templates/guides/quickstart/getting-started.md` still describe an older Claude-first prompt workflow, while `templates/guides/index.md`, `templates/TOOLS.md`, and `templates/engine/core/portable-foundation-spec.md` show the current Codex foundation model.
- 2026-05-11 — `CODEX.md` already links to the documentation hub, but several hub links are malformed markdown and should be fixed as part of the documentation-suite entrypoint repair.
- 2026-05-11 — PR #72 CI exposed one migrated-monolith reference introduced by the new user guide: `templates/USER-GUIDE.md` linked directly to fully migrated `templates/CONVENTIONS.md`. The fix is to link to the modular documentation standard instead.
