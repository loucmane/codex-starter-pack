# Decisions

- 2026-04-24 — Implement the first wizard slice as `python3 scripts/codex-task wizard kickoff` instead of a separate `codex-template` CLI.
- 2026-04-24 — Enforce the feature-branch prefix for the target task inside the wizard so kickoff fails early on the wrong branch.
- 2026-04-24 — Run initial `plan sync` automatically after kickoff scaffolding so the generated plan/tracker pair starts from a synced state.
