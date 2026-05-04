# Task 3 Scanner Foundation Audit

**Date**: 2026-04-26  
**Task**: 3 - Port SSOT Scanner Suite to Codex  
**Scope**: Current Codex scanner-suite reconciliation against stale Taskmaster/FPL assumptions and current foundation requirements.

## Executive Summary

Task 3 is not a first-time file copy from FPL MCP. The Codex repository already had a scanner suite under `scripts/template-ssot-scanner/`, and the safe implementation path was to reconcile current behavior against Taskmaster requirements and the newer portable foundation.

The audit found real gaps in the existing scanner suite:
- `run_all_scanners.py --help` executed scanner work instead of showing help.
- `find_duplicates.py --help` crashed because `%` characters in the argparse epilog were not escaped.
- `scanner.py` scanned local `.codex` runtime/cache/plugin state by default, inflating the scan from current foundation files to thousands of local artifacts.
- `analyze_references.py` and `find_duplicates.py` did not unwrap v2 metadata for `migration_status.json`, so migrated monolith checks silently used the wrong shape.
- `migration_detector.py` wrote incorrect metadata stats even though its printed summary was correct.
- Scanner outputs used a v2 metadata wrapper, but there was no JSON schema validation enforcing the wrapper contract.
- `templates/metadata/template-overview.md` held one direct reference to a fully migrated monolith (`templates/CONVENTIONS.md`), which became visible once metadata unwrapping was fixed.

## Current Suite Inventory

Current scanner modules after excluding generated output and Python caches:
- `scanner.py`
- `migration_detector.py`
- `analyze_references.py`
- `find_duplicates.py`
- `generate_fixes.py`
- `safe_reorganize.py`
- `scan_core.py`
- `scan_metadata.py`
- `report_generator.py`
- `validation_interface.py`
- `run_all_scanners.py`
- `test_cli_behavior.py`
- `test_metadata_compatibility.py`
- `test_integration.py`
- `test_ci_integration.sh`
- `README.md`

Evidence:
- `current-files.txt`
- `tracked-files.txt`
- `fpl-diff-summary.txt`

## FPL Comparison

FPL MCP remains useful as historical context only. The current Codex scanner suite already diverges from the FPL source in the core scanner modules and now includes Codex-specific hardening.

Diff-backed conclusion:
- Do not overwrite current Codex scanner files with FPL files.
- FPL-only `requirements.txt` is superseded by the repository Python dependency system from Task 2 (`pyproject.toml`, `uv.lock`, `requirements.lock`).
- Current implementation work should target proven runtime and metadata gaps, not broad file copying.

## Implemented Hardening

- Added real argparse handling to `run_all_scanners.py`, so `--help` exits safely without running scanners.
- Changed `run_all_scanners.py` to pass commands as argument lists instead of `shell=True`.
- Made `run_all_scanners.py` default to `--no-checkpoints`, with `--with-checkpoints` as an explicit opt-in.
- Aligned runner dependency checks to the repository Python baseline (`Python 3.11+`).
- Escaped `%` in `find_duplicates.py` help text to prevent argparse format-string failures.
- Added default exclusions in `scanner.py` for local Codex runtime/cache/plugin/generated state.
- Updated migration-status consumers to use `load_with_metadata`, preserving v1/v2 compatibility.
- Corrected `migration_detector.py` metadata stats for fully/partially/not migrated counts.
- Added JSON schema validation for v2 scanner output metadata through `jsonschema`.
- Extracted scanner file discovery into `scan_core.py`.
- Extracted metadata report writing/validation into `report_generator.py`.
- Added `validation_interface.py` for shared serializable validation findings and threshold severity mapping.
- Added `scanner_config.yaml` for configurable validation rules and severity levels.
- Wired configured validation findings into `analyze_references.py` output without making noisy broken-reference diagnostics fail the full runner by default.
- Replaced the stale direct `templates/CONVENTIONS.md` reference in `templates/metadata/template-overview.md` with a modular-convention note.
- Added pytest coverage for CLI help safety, default runtime exclusions, migration-status metadata unwrapping, and schema rejection of malformed v2 outputs.

## Verification Results

Targeted scanner regression tests:
- `18 passed`
- Evidence: `tests-2026-04-26-scanner.txt`
- Coverage evidence: `coverage-2026-04-26-scanner.txt`

Full scanner suite:
- `migration_detector.py`: passed
- `scanner.py`: passed
- `analyze_references.py`: passed
- `find_duplicates.py`: passed
- `generate_fixes.py`: passed
- Evidence: `run-all-2026-04-26-pass.txt`
- Severity finding evidence: `validation-findings-2026-04-26.txt`

Key current scanner metrics after runtime exclusions:
- Total scanned files: `318`
- Total scanned lines: `55677`
- Full runner wall time: `0:01.33`
- Full runner max RSS: `27548 KB`
- Broken references: `176`
- Circular dependencies: `11`
- Orphaned files: `67`
- References to fully migrated monoliths: `0`
- Duplicate groups: `2`
- Migration completion reported by duplicate finder: `37.5%`

## Remaining Taskmaster Alignment

Taskmaster subtasks should be interpreted through the stale-baseline lens:
- `3.1` is satisfied by this audit and evidence set.
- `3.2` is satisfied by a conservative modular extraction: scan discovery, report writing, and validation result interfaces were separated without rewriting scanner behavior.
- `3.3` versioned metadata output is satisfied for the scanner-output wrapper; this task corrected broken v2 consumers and metadata stats.
- `3.4` JSON schema validation is satisfied for the scanner-output wrapper.
- `3.5` is satisfied by `scanner_config.yaml`, configured validation rules, shared severity handling, and `analyze_references.py` validation findings.
- `3.6` legacy compatibility is partially present through `load_with_metadata`.
- `3.7` is satisfied by the focused pytest suite plus coverage evidence across CLI behavior, metadata/schema compatibility, scan core, migration detection, reference analysis, report writing, fix loading, and safe reorganization metadata loading.
- `3.8` is satisfied by the scoped scanner defaults, no-checkpoint runner default, and performance evidence showing the full runner completes in about 1.33 seconds with about 27 MB max RSS. Parallelism/caching are not justified at this size.

## Decision

The correct next boundary is Task 3 verification and closeout. The scanner suite is now safer and more Codex-aligned, Taskmaster subtasks are complete, and remaining work is to run repository guard/plan sync, update work-tracking, and mark the parent task done if verification stays green.
