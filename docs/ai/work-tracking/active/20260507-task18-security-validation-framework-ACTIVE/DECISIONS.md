# Decisions

- 2026-05-07 — Implement Task 18 as a portable scanner-suite security validator instead of a broad SAST framework. This keeps the work aligned with `templates/engine/core/portable-foundation-spec.md` and reuses `scan_core`, `PatternMatcher`, `ValidationFinding`, and metadata-wrapped report output.
- 2026-05-07 — Defer `detect-secrets`, generalized SAST integration, and sanitization helper APIs. None are current dependencies or proven consumers in this repository; adding them would expand runtime and maintenance scope without evidence.
- 2026-05-07 — Wire `security_validator.py` into `run_all_scanners.py` as a required scanner that reports findings but does not fail the suite on baseline findings. Remediation policy can be added later if the project wants thresholds to block.
- 2026-05-07 — Keep false-positive handling path/rule based through existing scanner allowlists instead of inventing a second allowlist system in Task 18.
