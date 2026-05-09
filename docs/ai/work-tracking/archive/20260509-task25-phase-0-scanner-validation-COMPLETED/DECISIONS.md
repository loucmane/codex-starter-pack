# Decisions

- 2026-05-09 — Implement Task 25 as a portable static Phase 0 scanner validation gate. It will consume existing scanner outputs and monitoring artifacts, classify pass/warn/fail, and write Markdown/JSON evidence under `reports/phase0-scanner-validation/`.
- 2026-05-09 — Do not rewrite scanner modules or mutate scanner runtime outputs merely to make the gate green. Warning-level scanner findings can remain visible without blocking strict mode unless policy later upgrades them to error-level checks.
- 2026-05-09 — Generate task-local implementation evidence under the active work-tracking folder, while the permanent report README and CI workflow point to `reports/phase0-scanner-validation/`. This avoids committing incidental runtime report churn during Task 25 verification.
