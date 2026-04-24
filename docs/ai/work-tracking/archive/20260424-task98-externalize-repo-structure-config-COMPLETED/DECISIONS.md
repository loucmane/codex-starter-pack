# Decisions

- 2026-04-24 — Use `.codex/config.toml` as the repo-local source of truth for path roots via a dedicated `[repo_structure]` section.
- 2026-04-24 — Keep the configuration root-based rather than file-by-file: derive `sessions/current`, `.taskmaster/tasks/tasks.json`, report directories, and work-tracking active/archive paths from the configured roots.
- 2026-04-24 — Introduce a small shared script helper (`scripts/_repo_structure.py`) instead of re-parsing `.codex/config.toml` independently in each workflow script.
