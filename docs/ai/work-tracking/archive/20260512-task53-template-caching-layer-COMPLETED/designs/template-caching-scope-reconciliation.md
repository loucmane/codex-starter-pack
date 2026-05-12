# Task 53 Scope Reconciliation - Template Caching Layer

## Purpose

Task 53 asks for a "Template Caching Layer" with Redis, distributed cache invalidation, startup warming, persistence, metrics, and debugging tools. That wording predates the portable foundation work completed in Tasks 8, 22, 28, and 61.

This scope gate reconciles the historical task text against the current repository so implementation stays evidence-backed and portable.

## Evidence Reviewed

- `scripts/template_registry.py` already provides `TemplateRegistry`, a TTL-backed in-process registry index cache, explicit `invalidate_cache()`, `warm_cache()`, cached template text reads via `_read_text_cached()`, resolution traces, and discovery-path metrics.
- `tests/meta_workflow_guard/test_template_registry.py` already covers registry discovery, search filters, compatibility resolution, deterministic miss suggestions, cache warming, TTL refresh, explicit invalidation, and real registry text reads.
- `scripts/template-performance-harness` already provides `template_registry_records` and `template_registry_warm_cache` probes.
- Task 8 implemented the reusable `TemplateRegistry` API and explicitly scoped the cache layer to a portable in-process TTL cache with explicit invalidation.
- Task 28 added registry observability for resolution paths (`discovery_metrics()` / `reset_discovery_metrics()`) and deterministic warm-cache reporting.
- Task 61 profiled the current registry, confirmed warm-cache lookup is already under the historical `<50ms` target, and rejected bloom filters, predictive prefetching, persistent caches, async APIs, and service/runtime discovery layers without future evidence.

## Current-State Gap

The repository does not need a new Redis cache, distributed invalidation system, or persistent cache for the current portable foundation.

The remaining useful gap is cache-layer observability:

- callers can warm the registry cache, invalidate it, and inspect discovery-path metrics
- callers cannot inspect index-cache hits, misses, rebuilds, invalidations, cache age, TTL expiry, or the `_read_text_cached()` LRU state
- the performance harness currently reports warm-cache success/failure counts but not cache diagnostics

That makes it harder to prove cache effectiveness without adding ad hoc instrumentation in tests or reports.

## Rejected Scope

The following historical Task 53 items are rejected for this pass unless future evidence proves a real need:

- Redis or any external cache service. The foundation must remain repo-local and portable.
- Distributed cache invalidation. There is no multi-process service topology in the current implementation.
- Persistent cache files. Task 61 already rejected persistent discovery caches because invalidation semantics are undefined for this portable foundation.
- Startup warming daemon or background worker. Current consumers instantiate the registry locally and can call `warm_cache()` directly.
- Parallel cache architecture outside `TemplateRegistry`. Tasks 8 and 61 selected and optimized the current registry path.

## Selected Implementation

Task 53 will add a narrow cache diagnostics layer to the existing `TemplateRegistry`:

1. Track index-cache hits, misses, rebuilds, and explicit invalidations.
2. Expose a structured `cache_stats()` snapshot with index cache state, TTL age/remaining time, record count, and read-text LRU cache info.
3. Reset cache counters predictably when requested.
4. Extend focused registry tests to prove stats are deterministic across hit, miss, TTL rebuild, invalidation, and text-read caching paths.
5. Extend the warm-cache performance probe message to include cache diagnostics without adding new runtime output files.

## Acceptance Criteria

- No Redis, distributed cache, persistence layer, background warming daemon, or new service runtime is introduced.
- `TemplateRegistry.cache_stats()` exposes deterministic, copy-safe diagnostics.
- Cache stats distinguish cold rebuild, warm hit, TTL rebuild, explicit invalidation, and cached text reads.
- Existing registry behavior remains unchanged.
- Focused tests and performance evidence are captured under `reports/template-caching-layer/`.
- Final evidence includes focused tests, performance harness, plan sync, work-tracking audit, guard validation, Taskmaster health, and diff check.

## S:W:H:E

- **2026-05-12 21:50 CEST** - [S:20260512|W:task53-template-caching-layer|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260512-task53-template-caching-layer-ACTIVE/designs/template-caching-scope-reconciliation.md] Reconciled Task 53 from historical Redis/distributed-cache wording to portable cache diagnostics on the existing `TemplateRegistry` cache layer.
