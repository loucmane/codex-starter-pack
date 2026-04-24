# Decisions

- 2026-04-24 — Keep bootstrap support inside `scripts/codex-task` instead of introducing a separate installer so adoption, kickoff, archive, and plan-sync flows remain on one helper surface.
- 2026-04-24 — Treat existing workflow directories and policy/config files as migration inputs; bootstrap should create missing assets by default and only overwrite with explicit force.
- 2026-04-24 — Generate a bootstrap setup note under `.codex/bootstrap/FOUNDATION-SETUP.md` so adoption guidance lives with the repo-local config rather than assuming a docs root layout.
