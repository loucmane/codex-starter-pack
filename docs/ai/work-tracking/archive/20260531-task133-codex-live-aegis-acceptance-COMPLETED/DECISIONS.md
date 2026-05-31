# Decisions

- 2026-05-31 — Keep the live product-task acceptance test fully isolated in `/tmp`; do not run it against HPFetcher or mutate the user's real project.
- 2026-05-31 — Use a real Codex client invocation for acceptance, with Aegis MCP supplied through command-scoped configuration. This avoids polluting the user's persistent Codex MCP registry while still testing the agent-agnostic path.
- 2026-05-31 — Prefer MCP-first guidance when an Aegis MCP server is present. CLI commands remain useful, but bootstrap guidance now says CLI fallback is only valid when `aegis` is already on PATH.
- 2026-05-31 — Treat Codex as a first-class primary agent, not as Claude-with-different-tools. Codex installs use explicit Aegis evidence logging rather than Claude pending-hook consumption.
- 2026-05-31 — Normalize user-supplied kickoff slugs by stripping a leading `task-<id>-` or `<id>-` prefix. Agents often include the task id in their slug guess, while Aegis already prefixes branch/session paths with the task id.
