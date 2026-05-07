# Task 28 Dual-Path Discovery – Implementation Notes

## Planned Workstreams
- Scope reconciliation: complete. Task 28 extends `TemplateRegistry.resolve()` rather than creating a parallel discovery engine.
- Registry observability: complete. `ResolutionResult` now carries a structured `trace`, and `TemplateRegistry.discovery_metrics()` / `reset_discovery_metrics()` expose instance-level counts for modular, compatibility, legacy, Serena fallback, and error paths.
- Cache warming: complete. `TemplateRegistry.warm_cache()` resolves common queries and reports successes/failures without raising on misses.
- Discovery hints: complete. Misses now include deterministic local suggestions from registry IDs, paths, titles, tags, and compatibility mappings.
- Verification: focused registry evidence captured at `reports/dual-path-discovery/tests-2026-05-07-template-registry.txt` (`9 passed`).
