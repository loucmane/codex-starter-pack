# Decisions

- 2026-05-09 — Treat Task 27 as a reconciliation task, not a blind rewrite. The existing pattern modules stay in place because current evidence shows the monolith extraction already happened.
- 2026-05-09 — Add `templates/patterns/index.md` as the canonical modular pattern-family index and redirect legacy `templates/PATTERNS.md` compatibility lookup to that file instead of a bare directory.
- 2026-05-09 — Bring `templates/patterns/**/*.md` under the portable metadata policy so future pattern drift is caught by guard/tests instead of relying on memory or manual review.
- 2026-05-09 — Treat Taskmaster mutation commands as serial operations only. Parallel reads are fine, but concurrent Taskmaster writes can race on `.taskmaster/tasks/tasks.json`.
