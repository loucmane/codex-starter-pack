# Task 3 Port SSOT Scanner Suite to Codex – Implementation Notes

## Planned Workstreams
- Audit current scanner modules, tests, outputs, and generated runtime artifacts.
- Compare current capabilities against Taskmaster subtasks 3.1-3.8.
- Compare current capabilities against the broader Codex foundation requirements: guard, metadata policy, template drift detection, metrics, repo-structure portability, and bootstrap/adoption workflows.
- Document which stale migration requirements are already satisfied by current code.
- Implement only confirmed remaining scanner foundation gaps.

## Scope Gate
- Completed before scanner implementation: Task 3 is constrained to evidence-backed foundation reconciliation, not broad source copying from FPL MCP.

## Completed Implementation
- Fixed unsafe CLI behavior in `run_all_scanners.py` and `find_duplicates.py`.
- Changed the full runner to avoid `shell=True` and default to no checkpoint generation.
- Added default scanner exclusions for local Codex runtime/cache/plugin paths.
- Added `scan_core.py`, `report_generator.py`, and `validation_interface.py` to create modular scanner seams without a broad rewrite.
- Added `scanner_config.yaml` and configured validation findings in `analyze_references.py`.
- Added JSON schema validation for v2 scanner-output metadata through `jsonschema`.
- Fixed v2 metadata unwrapping in `analyze_references.py`, `find_duplicates.py`, and `safe_reorganize.py`.
- Corrected `migration_detector.py` metadata stats.
- Replaced the stale `templates/CONVENTIONS.md` reference in `templates/metadata/template-overview.md`.
- Added focused pytest coverage for CLI safety, runtime exclusions, metadata/schema compatibility, scanner module behavior, fix-generator loading, and safe-reorganization metadata loading.

## Evidence
- Audit: `reports/ssot-scanner-suite/scanner-foundation-audit.md`
- Full runner: `reports/ssot-scanner-suite/run-all-2026-04-26-pass.txt`
- Tests: `reports/ssot-scanner-suite/tests-2026-04-26-scanner.txt`
- Coverage: `reports/ssot-scanner-suite/coverage-2026-04-26-scanner.txt`
- Performance: `reports/ssot-scanner-suite/perf-run-all-2026-04-26.txt`
