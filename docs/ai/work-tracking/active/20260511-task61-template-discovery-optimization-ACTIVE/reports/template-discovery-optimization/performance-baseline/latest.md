# Template Performance Report

Generated: 2026-05-11T13:17:21.726885+02:00
Policy version: 1.0.0
Status: fail

## Summary
- Total checks: 4
- Passed: 3
- Warnings: 0
- Errors: 1

## Checks
- template_registry_records: pass
  - Probe: `template_registry_records`
  - Elapsed: `0.106938s`
  - Thresholds: warning `0.150000s`, critical `0.350000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Discovered 261 template registry records
- template_registry_warm_cache: pass
  - Probe: `template_registry_warm_cache`
  - Elapsed: `0.028395s`
  - Thresholds: warning `0.050000s`, critical `0.250000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Warmed 3 query result(s), 0 failure(s)
- codex_guard_validate: fail
  - Probe: `command`
  - Elapsed: `0.199795s`
  - Thresholds: warning `5.000000s`, critical `10.000000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `1`
  - Message: Probe returned nonzero exit code 1
- scanner_no_checkpoints: pass
  - Probe: `command`
  - Elapsed: `0.648865s`
  - Thresholds: warning `10.000000s`, critical `20.000000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Command completed
