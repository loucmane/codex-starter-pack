# Findings

## Discoveries
- Historical reports (2025-08) highlight dangerous legacy scripts (`reorganize_files.sh`) and confirm the safety features we must preserve (`safe_reorganize.py`, consolidated reference fixer).
- Codex templates still rely heavily on Serena MCP tooling; documentation updates must reinforce that rather than remove it.

## Test Results
- `python3 scripts/template-ssot-scanner/scanner.py --base /home/loucmane/codex --no-checkpoints` ✅ (237 files; outputs in `output/data/`).
- `python3 scripts/template-ssot-scanner/analyze_references.py` ✅ (181 broken refs, 10 circular deps baseline).
- `python3 scripts/template-ssot-scanner/find_duplicates.py --generate-diffs --section-matching` ✅ (duplicate_analysis.json; overall migration 9%).
- `python3 scripts/template-ssot-scanner/migration_detector.py` ✅ (migration_status.json confirms 4 fully migrated files, etc.).
- `python3 scripts/template-ssot-scanner/generate_fixes.py` ✅ (fix_recommendations.json + scripts in `output/scripts/`).
- `python3 scripts/template-ssot-scanner/safe_reorganize.py` ✅ (dry-run; no moves proposed; report in `scripts/template-ssot-scanner/output/reports/`).

## Performance Observations
- Scanner run inside Codex repo completed in ~0.2s (thanks to limited file set and local execution).

## Issues Encountered
- Optional packages for sequential thinking/fpl MCP still need manual installation; tracked separately.
- Migration status reports show majority of monolithic files still partially/not migrated (needs remediation via generated scripts).

## Proposed Solution: codex-task + Diff-Aware Guard (2025-09-20 15:27)
- Build `codex-task <workflow>` helpers that:
  - Run Serena registry lookup for the appropriate handler.
  - Display handler checklist + copy relevant snippet.
  - Scaffold S:W:H:E entries in session/work-tracking docs with real timestamps.
  - Invoke `codex-guard --validate` on completion.
- `codex-guard` responsibilities:
  - Diff-aware checks for handler references, template structure, evidence (file:line / command output), timestamp/branch accuracy.
  - Uses Serena to confirm handler IDs exist in the registry.
  - Supports `--auto-fix` to insert skeleton blocks when safe and surfaces remediation tips.
- Integration plan: expose commands locally, optionally add pre-commit/CI hooks once stable.
