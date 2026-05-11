# Decisions

- 2026-05-11 — Treat Task 37's historical OpenTelemetry/Grafana/Elasticsearch wording as stale service-oriented context. The current portable foundation should keep telemetry file-based, script-driven, and CI-friendly unless a real long-running service exists.
- 2026-05-11 — Implement Task 37 as a first-class static telemetry pipeline contract: add `--kind telemetry` as a semantic alias for the existing full report chain, preserve `--kind all`, and document the stage outputs centrally instead of adding duplicate observability infrastructure.
