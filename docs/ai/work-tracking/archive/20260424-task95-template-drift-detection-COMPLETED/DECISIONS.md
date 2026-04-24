# Decisions

- 2026-04-24 — Implement drift detection as a new `python3 scripts/codex-guard drift-check` subcommand so the feature stays inside the existing enforcement entrypoint.
- 2026-04-24 — Generate both human-readable and machine-readable outputs under `reports/template-drift/`, while preserving task-local verification logs under the Task 95 active folder.
- 2026-04-24 — Keep Task 95 scoped to deterministic drift classes that can be validated against current metadata and canonical-doc rules; reserve broader wizard/dashboard concerns for Tasks 96 and 97.
- 2026-04-24 — Run `drift-check --strict` in both guard workflows so drift becomes part of the normal automation path rather than an optional local check.
