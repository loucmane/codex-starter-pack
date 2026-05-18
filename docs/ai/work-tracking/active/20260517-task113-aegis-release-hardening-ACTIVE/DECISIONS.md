# Decisions

- 2026-05-17 — Task 113 will extend the Task 112 invocation contract rather than replace it. Local checkout commands, editable package installs, `scripts/codex-task aegis ...`, and development MCP startup remain supported.
- 2026-05-17 — Use `aegis-foundation` as the working public distribution name until package-name or release-policy checks identify a better option. Keep console commands `aegis` and `aegis-mcp-server` stable unless a concrete collision is found.
- 2026-05-17 — Treat PyPI publication as out of scope for this task. The task must make local wheel/sdist, package metadata, `uvx`/`pipx` snippets, signing policy, update/rollback guidance, and CI templates release-ready and test-backed.
- 2026-05-17 — Keep `pyproject.toml` version literal for now and enforce alignment with `aegis_foundation.version` through deterministic tests. A fully dynamic package version can be revisited if release tooling later needs it.
- 2026-05-18 — Keep the Task 113 ACTIVE work-tracking folder open until PR #113 merges. Daily session rollover uses `scripts/codex-task sessions continue`; archive happens only after merge in a separate follow-up commit.
