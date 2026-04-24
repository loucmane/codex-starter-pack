# Findings

- 2026-04-24 — The archived wizard draft is broader than the current repo needs; a kickoff-focused wizard covers the highest-friction workflow while staying deterministic.
- 2026-04-24 — `scripts/codex-task` is the correct home for the wizard because it already owns session/work-tracking/plan operations and can preserve their existing file formats.
- 2026-04-24 — Seeding `plan sync` inside the wizard makes the initial state immediately compatible with guard expectations.
