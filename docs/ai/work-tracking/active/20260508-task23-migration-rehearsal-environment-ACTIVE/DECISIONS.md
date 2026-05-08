# Decisions

- 2026-05-08 — Implement Task 23 as `codex-task rehearsal plan`, a non-destructive planner that consumes migration roadmap JSON plus rollback checkpoint JSON and emits a rehearsal manifest/runbook. Defer Docker, external API keys, agent simulators, k6/locust, and automatic worktree creation because no current repository evidence justifies those stateful layers.
