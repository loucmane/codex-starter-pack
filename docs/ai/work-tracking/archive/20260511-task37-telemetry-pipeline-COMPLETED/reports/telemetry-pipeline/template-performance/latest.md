# Template Performance Report

Generated: 2026-05-11T17:18:30.402357+02:00
Policy version: 1.0.0
Status: fail

## Summary
- Total checks: 4
- Passed: 2
- Warnings: 1
- Errors: 1

## Checks
- template_registry_records: pass
  - Probe: `template_registry_records`
  - Elapsed: `0.080973s`
  - Thresholds: warning `0.150000s`, critical `0.350000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Discovered 261 template registry records
- template_registry_warm_cache: warn
  - Probe: `template_registry_warm_cache`
  - Elapsed: `0.052710s`
  - Thresholds: warning `0.050000s`, critical `0.250000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Elapsed time exceeded warning threshold 0.050000s
- codex_guard_validate: fail
  - Probe: `command`
  - Elapsed: `0.176367s`
  - Thresholds: warning `5.000000s`, critical `10.000000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `1`
  - Message: Probe returned nonzero exit code 1
- scanner_no_checkpoints: pass
  - Probe: `command`
  - Elapsed: `0.734485s`
  - Thresholds: warning `10.000000s`, critical `20.000000s`
  - Baseline: `n/a`
  - Regression: `n/a`
  - Return code: `0`
  - Message: Command completed
