# Task 61 Scope Reconciliation - Template Discovery Optimization

## Purpose

Task 61 asks for broad discovery optimization work: bloom filters, predictive prefetching, discovery result caching, file I/O optimization, async discovery API, metrics, and debugging mode. That wording predates the current portable foundation and the completed template registry/discovery work from Tasks 8 and 22.

This scope gate reconciles Task 61 against the current codebase so implementation stays evidence-backed.

## Evidence Reviewed

- `scripts/template_registry.py` now provides `TemplateRegistry`, `TemplateDiscoveryAPI`, registry index loading, compatibility lookup, search, resolution tracing, TTL index caching, explicit cache invalidation, cached template text reads, warm-cache reporting, and discovery metrics.
- `tests/meta_workflow_guard/test_template_registry.py` already covers registry discovery, search filters, compatibility resolution, suggestions, cache TTL/invalidation, warm lookup, and real registry reads.
- `scripts/template-performance-harness` already includes `template_registry_records` and `template_registry_warm_cache` probes.
- `templates/metadata/template-performance-policy.json` sets performance thresholds for registry record discovery and warm-cache resolution.
- Task 22 rejected REST/Redis/GraphQL discovery surfaces and selected an in-process `TemplateDiscoveryAPI` facade. Task 61 should not reverse that decision without new evidence.
- Task 45 established the current optimization pattern: profile first, then implement the smallest proven current-state gap.

## Baseline Evidence

Stored baseline artifacts:

- `reports/template-discovery-optimization/performance-baseline-2026-05-11.txt`
- `reports/template-discovery-optimization/performance-baseline/latest.json`
- `reports/template-discovery-optimization/registry-profile-baseline-2026-05-11.txt`
- `reports/template-discovery-optimization/registry-cold-baseline-samples-2026-05-11.txt`

Observed results:

- Performance harness `template_registry_records`: `0.106938s` in the first full harness run, passing the current policy threshold but above the historical `<50ms` task target.
- Performance harness `template_registry_warm_cache`: `0.028395s`, already below `<50ms`.
- Focused cold registry samples after filesystem cache warm-up: median `0.027335s`, max `0.028263s`, 261 records.
- Instrumented registry build: 362 frontmatter calls for 261 unique paths, with 101 duplicate frontmatter paths. The duplicate paths come from loading modular registry entries and then rediscovering the same markdown files during fallback markdown discovery.

The useful current-state gap is therefore not missing caching or a missing API. It is duplicate frontmatter work during index construction.

## Rejected Scope

The following historical Task 61 items are rejected for this pass unless future evidence proves a bottleneck:

- Bloom filters. The registry currently has direct dictionaries for `by_id` and `by_path`, and misses are not the measured bottleneck.
- Predictive prefetching. `TemplateRegistry.warm_cache()` already exists and warm-cache lookup is under 50ms.
- New persistent discovery result caching. The registry already has TTL cache and explicit invalidation; persistent cache invalidation semantics are undefined for this portable foundation.
- Async discovery API. Current consumers are local CLI/test/runtime helpers; async would add a second API surface without a measured concurrency problem.
- New service/runtime discovery layer. Task 22 explicitly chose an in-process facade over REST/GraphQL/Redis.

## Selected Implementation

Task 61 will implement a narrow registry-index optimization:

1. Avoid duplicate frontmatter reads/parses for markdown paths already loaded from `templates/registry/index.json`.
2. Preserve existing registry behavior and resolution ordering.
3. Add tests proving modular records are not reparsed during fallback markdown discovery.
4. Add performance evidence showing registry record discovery and warm-cache resolution remain under the current policy and the focused `<50ms` target on the current repo.

This keeps Task 61 aligned with the portable foundation: optimize the existing registry discovery path rather than introducing a parallel discovery system.

## Acceptance Criteria

- The duplicate frontmatter-call gap is covered by a focused regression test.
- Existing registry behavior tests remain green.
- Performance harness passes after the scope plan is synced.
- Final evidence includes focused tests, performance harness, plan sync, work-tracking audit, guard validation, Taskmaster health, and diff check.

## S:W:H:E

- **2026-05-11 13:24 CEST** — [S:20260511|W:task61-template-discovery-optimization|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260511-task61-template-discovery-optimization-ACTIVE/designs/template-discovery-optimization-scope-reconciliation.md] Reconciled Task 61 from broad historical optimization wording to duplicate frontmatter-work removal in the current `TemplateRegistry` index build.
