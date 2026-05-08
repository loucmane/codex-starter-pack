# Task 45 Scope Reconciliation - Scanner Optimization

## Purpose

Task 45 asks for broad scanner performance work: multiprocessing, incremental scanning, cache invalidation, regex optimization, streaming JSON, memory profiling, profiling mode, and lazy loading. That wording predates the current portable foundation and the completed scanner-suite foundation work from Task 3.

Task 45 must therefore optimize the current scanner in the smallest evidence-backed way instead of reintroducing a heavyweight scanner architecture.

## Current Baseline

Task 3 already completed the scanner-suite foundation and explicitly deferred broad parallelism/caching because the suite was reduced to a small, safe runtime after CLI and artifact cleanup. Its completed decision record says not to add parallelism/caching for Task 3 because runtime exclusions and no-checkpoint execution reduced the full runner to about 1.33 seconds.

Current code evidence:

- `scripts/template-ssot-scanner/scanner.py` scans `templates/`, `.codex`, and `.claude`, writes metadata-wrapped results, and already measures total scan duration in `save_scanner_report`.
- `scripts/template-ssot-scanner/scan_core.py` centralizes file discovery, include/exclude handling, and config-dir discovery.
- `scripts/template-ssot-scanner/run_all_scanners.py` runs the suite without checkpoints by default.
- `scripts/template-ssot-scanner/output/data/template_scan_results.json` currently reports `metadata.stats.files_scanned = 0`, `handlers_found = 0`, `references_found = 0`, and `issues_detected = 0` even though `data.scan_metadata.total_files` and `total_lines` are populated. That makes performance/report comparison less useful than the current foundation expects.
- `collect_scannable_files()` currently performs one recursive glob per configured suffix. The default suffix set is small, but config can expand it, and a single traversal is a safer large-repo baseline.

## Rejected Scope

The following historical details are not appropriate for this task without new evidence:

- `multiprocessing.Pool` parallelism. The scanner suite is currently fast enough that parallelism would add ordering, output, and platform complexity before a measured bottleneck exists.
- Persistent incremental cache and invalidation. The current foundation does not define cache storage, invalidation semantics, or CI behavior for scanner cache artifacts.
- Streaming JSON output. Current metadata-wrapped outputs are consumed as whole JSON documents by downstream scripts.
- Lazy loading for file contents. Reference extraction and metadata extraction both need complete file content today.
- Memory profiler integration. This belongs only after a concrete memory bottleneck is measured.

## Selected Implementation

Task 45 will implement conservative optimization support in two parts:

1. Optimize file discovery to use a single deterministic traversal and suffix filtering rather than one recursive traversal per suffix.
2. Add scanner profiling/reporting support so the scanner can expose truthful metadata stats and optional per-directory/per-file timing when `--profile-scan` is requested.

This directly addresses the current large-scale operation gap: scanner runs can now be compared through real metadata stats and optional slowest-file/discovery timings, while the default behavior stays simple and stable.

## Test Plan

- Add focused tests for deterministic single-pass discovery behavior.
- Add focused tests for profiling metadata on `TemplateScanner`.
- Add a CLI regression test proving scanner metadata stats are no longer zero for a real scan.
- Run the scanner-focused pytest subset and the full project pytest suite.
- Capture scanner profiling output and verification logs under `reports/scanner-optimization/`.

## S:W:H:E

- **2026-05-08 19:52 CEST** — [S:20260508|W:task45-scanner-optimization|H:docs/scope|E:docs/ai/work-tracking/active/20260508-task45-scanner-optimization-ACTIVE/designs/scanner-optimization-scope-reconciliation.md] Reconciled Task 45 from broad historical optimization wording to conservative scanner discovery/profile instrumentation grounded in the current portable foundation.
