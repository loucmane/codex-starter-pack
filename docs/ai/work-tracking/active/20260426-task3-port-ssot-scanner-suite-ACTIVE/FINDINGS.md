# Findings

- 2026-04-26 — Task 3 is likely another stale-baseline task. The repository already contains `scripts/template-ssot-scanner/`, so the first deliverable is an audit/reconciliation before any copy/refactor work.
- 2026-04-26 — Guard requires the scope gate to be completed before implementation work; the Task 3 plan now treats scope as defining reconciliation boundaries, while the scanner audit itself belongs to implementation.
- 2026-04-26 — Task 3 is broader than the old FPL MCP port wording. Later foundation work added guard integration, metadata policy, template drift detection, repo-structure portability, metrics, and cross-project adoption requirements that the scanner audit must account for.
- 2026-04-26 — The current scanner suite already existed and should not be overwritten by the FPL baseline. The safe path was targeted hardening: CLI safety, runtime exclusions, metadata compatibility, schema validation, severity configuration, tests, and performance verification.
- 2026-04-26 — Fixing v2 migration-status unwrapping exposed one real migrated-monolith reference in `templates/metadata/template-overview.md`; replacing it with a modular-conventions note allowed the full scanner suite to pass without suppressing the rule.
- 2026-04-26 — `safe_reorganize.py` still read scanner JSON directly and would misread wrapped v2 outputs; it now uses `load_with_metadata` like the other consumers.
