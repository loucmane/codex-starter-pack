# Findings

- 2026-05-13 — Historical Task 51 wording is stale for this foundation. Runtime decorators, persistent data models, live dashboards, anomaly services, and predictive capacity planning conflict with the repo's static, file-backed telemetry model.
- 2026-05-13 — Existing Task 97 and Task 37 work covers broad workflow telemetry, but there is no template-specific usage report that maps registered template IDs/paths/aliases to workflow evidence.
- 2026-05-13 — Task 8's `TemplateRegistry` is the correct source for registered template metadata; direct filesystem-only scans would miss registry aliases, statuses, and categories.
- 2026-05-13 — The live usage analytics report scanned 312 workflow files, found 735 template mentions across 106 templates, and left 149 registered templates with zero observed workflow references in the default non-archive scan.
