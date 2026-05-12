# Template Performance Report

Generated: 2026-05-12T21:56:57.581280+02:00
Policy version: 1.0.0
Status: pass

## Summary
- Total checks: 4
- Passed: 4
- Warnings: 0
- Errors: 0

## Checks
- template_registry_records: pass
  - Probe: `template_registry_records`
  - Elapsed: `0.099323s`
  - Thresholds: warning `0.150000s`, critical `0.350000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Discovered 261 template registry records
- template_registry_warm_cache: pass
  - Probe: `template_registry_warm_cache`
  - Elapsed: `0.023222s`
  - Thresholds: warning `0.050000s`, critical `0.250000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Warmed 3 query result(s), 0 failure(s); cache hits=2, misses=1, rebuilds=1, records=261
- codex_guard_validate: pass
  - Probe: `command`
  - Elapsed: `0.213261s`
  - Thresholds: warning `5.000000s`, critical `10.000000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Command completed
- scanner_no_checkpoints: pass
  - Probe: `command`
  - Elapsed: `0.673969s`
  - Thresholds: warning `10.000000s`, critical `20.000000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Command completed
