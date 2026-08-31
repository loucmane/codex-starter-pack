# Decisions

- 2026-08-31 — Preserve `/home/loucmane/codex` byte-for-byte. Retirement means deny new mutation, not rename, delete, clean, reset, or rewrite the historical checkout or its worktrees.
- 2026-08-31 — Use one versioned `root-policy.json` and one pure evaluator for `project_context.py`, Codex, and Claude. Do not duplicate path logic between adapters.
- 2026-08-31 — Install the mutation guard at user scope because project-local hooks disappear when a project is untrusted. Marking the old Codex project untrusted is defense in depth, not the active enforcement mechanism.
- 2026-08-31 — Cover all mutation-capable tool surfaces for sessions whose Git common root is retired; keep read-only inspection available. Unmanaged repositories are unaffected.
- 2026-08-31 — Update only the old Codex trust entry and only Claude's top-level Aegis package source. Preserve unrelated settings, modes, and exact rollback copies; trust only the exact Codex user hook through the supported app-server API.
- 2026-08-31 — Archived through the supported archive helper; no evidence was deleted.
