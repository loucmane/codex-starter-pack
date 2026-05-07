# Decisions

- 2026-05-07 — Queue-jump Task 107 ahead of Task 10. Rationale: this is a system-behavior correction triggered by a live workflow regression, and leaving the stale GAC-default guidance in place would keep affecting every later task.
- 2026-05-07 — Treat `gac` as explicit-request only. Rationale: Codex can use normal `git add`, `git commit`, `git push`, and GitHub commands directly when delegated and auth is available; the alias is user convenience, not agent infrastructure.
- 2026-05-07 — Add guard coverage for stale GAC-default language. Rationale: documentation alone is not enough; the guard should fail if commit guidance reintroduces the old default.
- 2026-05-07 — Expand guard scope beyond the initial commit-format files. Rationale: a future session can consult indexes and tool matrices before the leaf commit docs, so those files must also carry the same response-mode contract.
