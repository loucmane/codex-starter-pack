# Template Monitoring Reports

This directory stores static monitoring outputs from:

```bash
python3 scripts/template-monitoring
```

## Output Files

- `latest.md` - human-readable monitoring report
- `latest.json` - machine-readable monitoring payload for automation

## Scope

Monitoring consumes the metrics dashboard payload from `reports/template-metrics/latest.json` and evaluates it against `templates/metadata/template-monitoring-policy.json`.

The current implementation is static and file-based. It is designed for this portable foundation repository and for projects bootstrapped from it. It does not require Prometheus, Grafana, StatsD, Elasticsearch, a database, or a running web service.

## Local Usage

```bash
python3 scripts/template-metrics-dashboard
python3 scripts/template-monitoring --strict
```

Use `--strict` when error-level findings should fail the command. Warning-level findings remain visible in the report without failing strict mode.
