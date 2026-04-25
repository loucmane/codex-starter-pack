# Scanner Suite Capability Assessment

**Generated**: 2026-04-25 13:50 CEST
**Source**: `scripts/template-ssot-scanner/run_all_scanners.py`

## Components
- `migration_detector.py` - detects migration status for template monolith/index files.
- `scanner.py` - scans templates and Codex/Claude configuration into metadata-wrapped JSON.
- `analyze_references.py` - builds reference and dependency analysis from scanner output.
- `find_duplicates.py` - detects duplicate content and section mappings.
- `generate_fixes.py` - generates fix recommendations and shell/Python fix scripts.
- `scan_metadata.py` - loads/saves metadata-wrapped scanner outputs.
- `safe_reorganize.py` - migration-aware file move/reorganization helper.

## Full Suite Result
- `migration_detector.py`: completed
- `scanner.py`: completed
- `analyze_references.py`: completed
- `find_duplicates.py`: completed
- `generate_fixes.py`: completed

## Scanner Output Summary
- Migration detector analyzed 11 candidate files.
- Migration detector classified 4 files as fully migrated, 5 as partially migrated, and 2 as not migrated.
- Main scanner scanned 2205 files and 278825 lines.
- Reference analyzer reported 1180 broken references, 17 circular dependencies, and 1757 orphaned files.
- Duplicate finder reported 18 exact duplicate groups and 1 partial duplicate.
- Fix generator produced 1180 broken-reference fix recommendations and 19 duplicate-removal recommendations.

## Operational Findings
- `run_all_scanners.py --help` executed the full suite instead of showing help, so the orchestrator does not expose a safe help path.
- `find_duplicates.py --help` crashes with `TypeError: not enough arguments for format string`, so its argparse help text has an unescaped percent sign or formatting bug.
- The default scanner scope includes runtime/plugin/cache paths such as `.codex/.tmp`, which inflates broken-reference and duplicate counts.
- Scanner checkpoints generated roughly 177MB of untracked data during one run, so generated checkpoint/data/script outputs should not be committed by default.

## Capability Verdict
The scanner suite is useful for broad migration and dependency analysis, but its default output is too noisy for direct enforcement. Task 1 should treat these outputs as diagnostic inputs, then filter or scope them before turning findings into downstream tasks.
