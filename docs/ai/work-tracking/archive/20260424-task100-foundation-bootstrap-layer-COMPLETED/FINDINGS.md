# Findings

- 2026-04-24 — The guided kickoff flow still generates generic wizard-oriented plan and tracker text, so Task 100 requires a manual baseline rewrite before implementation starts.
- 2026-04-24 — Task 99 intentionally stopped at the portable specification boundary; Task 100 must turn that contract into starter assets and migration-safe bootstrap behavior.
- 2026-04-24 — A repo-local `.codex/config.toml` plus the portable metadata policy file are sufficient starter assets for bootstrap; the rest of the workflow surface can be derived from `[repo_structure]` and scaffolded as directories.
- 2026-04-24 — Migration-safe bootstrap behavior is easiest to reason about when existing config/policy files are skipped by default and only refreshed under explicit `--force`.
