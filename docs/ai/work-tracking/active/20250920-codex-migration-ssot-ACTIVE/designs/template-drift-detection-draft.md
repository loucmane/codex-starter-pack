# Template Drift Detection (Draft)

## Objective
Automatically detect when implementation drifts from template specifications and provide actionable reconciliation guidance.

## Approach
1. Parse templates and target files (AST + structure heuristics).
2. Compare current state against template expectations.
3. Report drift percentage and affected sections.
4. Integrate with enforcement framework (guard + dashboard).

## Tasks
- Gather template → file mappings.
- Implement AST/diff comparison (`scripts/codex-guard drift-check`).
- Produce drift report (CLI + JSON).
- Hook into guard (threshold-based warnings/blocking).
- Store metrics for dashboard.

## Open Questions
- Granularity of drift measurement (file, section, block?).
- Auto-fix suggestions vs. manual reconciliation.
- Performance considerations for large repos.
