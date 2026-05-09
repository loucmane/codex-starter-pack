# Phase 0 Scanner Validation Reports

This directory stores static Phase 0 scanner validation outputs from:

```bash
python3 scripts/template-phase0-validation
```

## Output Files

- `latest.md` - human-readable Phase 0 validation report
- `latest.json` - machine-readable validation payload for automation

## Scope

Phase 0 validation consumes existing scanner outputs from `scripts/template-ssot-scanner/output/data/` and the static monitoring payload from `reports/template-monitoring/latest.json`.

The evaluator is deliberately file-based. It does not rerun scanners, rewrite scanner outputs, hide known warnings, require a web service, or schedule stakeholder review meetings. It aggregates the current scanner evidence into one repeatable gate that can be generated locally and in CI.

## Local Usage

```bash
python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci
python3 scripts/template-metrics-dashboard
python3 scripts/template-monitoring --strict
python3 scripts/template-phase0-validation --strict
```

Or run the full report chain:

```bash
python3 scripts/codex-task report generate --kind all --strict-drift --strict-monitoring --strict-phase0
```

`--strict` fails only on error-level Phase 0 findings. Warning-level scanner, security, baseline, or monitoring findings remain visible in the report without failing strict mode.
