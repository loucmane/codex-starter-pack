# SSOT Scanner Summary — 2025-09-20

## Outputs
- `output/data/template_scan_results.json` — baseline (237 files).
- `output/data/reference_analysis.json` — 181 broken references, 10 circular dependencies.
- `output/data/duplicate_analysis.json` — overall migration 9%; MATRICES mostly migrated.
- `output/data/migration_status.json` — 4 fully migrated files (WORKFLOWS, PATTERNS, CONVENTIONS, BUILDING-BETTER); 5 partial; 2 not migrated.
- `output/data/fix_recommendations.json` + `output/scripts/` — 181 reference fixes generated.
- `scripts/template-ssot-scanner/output/reports/safe_reorg_*.json` — no safe relocations proposed.

## Next Actions
1. Implement `codex-task` helper + diff-aware guard (`codex-task-guard-plan.md`).
2. Apply generated reference fixes (review scripts, run with `--dry-run` first).
3. Address circular dependencies & orphaned files flagged in reports.
4. Update FINDINGS/CHANGELOG/Tracker once remediation tasks begin.
