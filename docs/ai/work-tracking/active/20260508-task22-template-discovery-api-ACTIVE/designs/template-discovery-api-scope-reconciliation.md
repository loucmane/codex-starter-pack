# Task 22 Template Discovery API Scope Reconciliation

## Purpose

Task 22 predates the completed portable-foundation work, so its original wording must be reconciled before implementation. The historical task text asks for a REST-like API, Redis/LRU caching, GraphQL schema, filtering, pagination, and dependency access. Current repository evidence shows that most discovery infrastructure already exists as an in-process Python registry, not a service.

This scope gate defines the current implementation boundary for Task 22.

## Evidence Reviewed

- `templates/engine/core/portable-foundation-spec.md` defines the current architecture as portable core logic plus repo-local adapter configuration.
- `docs/ai/work-tracking/archive/20260430-task4-scanner-configuration-system-COMPLETED/designs/backlog-alignment-audit.md` says pending Tasks 4-80 must treat old details as suspect and complete a scope-reconciliation gate before implementation.
- `.taskmaster/tasks/task_022.txt` still contains the older REST, Redis, and GraphQL wording.
- `scripts/template_registry.py` already provides `TemplateRegistry`, `TemplateRecord`, in-memory TTL cache, compatibility mapping, resolve fallback, metadata parsing, text reading, warm-cache reporting, and search by id/type/category/tags/text.
- `tests/meta_workflow_guard/test_template_registry.py` already covers registry discovery, search filters, compatibility resolution, cache TTL/invalidation, cache warming, suggestions, and real registry reads.
- `templates/registry/index.json` is the current modular registry source, while template frontmatter carries title/type/status/category/tags/dependencies/version metadata.

## Current-State Findings

1. A greenfield REST or GraphQL service would not match the current portable-foundation layer. The core system is CLI/script-driven and configuration-backed, with no service runtime in the repo.
2. Redis is out of scope for this repo. `TemplateRegistry` already uses thread-safe in-memory TTL caching and cached text reads, which is sufficient for the current foundation.
3. The useful remaining gap is a stable programmatic facade around `TemplateRegistry` that returns serializable data structures suitable for CLI, tests, future MCP/plugin adapters, and possible later service wrappers.
4. Dependency data is already present in template frontmatter, but there is no first-class API method that exposes it in normalized form.
5. Pagination and status/version filtering are not first-class in `TemplateRegistry.search`; adding them to the facade avoids broad changes to the registry core while satisfying the useful part of Task 22.

## Decision

Implement an in-process `TemplateDiscoveryAPI` facade in `scripts/template_registry.py`.

The facade will:

- wrap an existing `TemplateRegistry` instance or create one from `repo_root`
- expose `get_template(template_id)`
- expose `search_templates(...)` with query/text, category, type, status, version, tags, limit, and offset
- expose `list_by_category(category, ...)`
- expose `get_dependencies(template_id)`
- return JSON-serializable dictionaries with pagination metadata
- reuse `TemplateRegistry` cache and search behavior instead of adding Redis or a service runtime

## Non-Goals

- Do not add a REST server.
- Do not add Redis or another external cache dependency.
- Do not add GraphQL schema/runtime.
- Do not fork the existing registry discovery path.
- Do not change repo-structure assumptions outside the existing portable config model.

## Implementation Boundary

Expected code surface:

- `scripts/template_registry.py`
- `tests/meta_workflow_guard/test_template_registry.py` or a focused companion test file under `tests/meta_workflow_guard/`
- Task 22 work-tracking/session/plan updates
- Taskmaster Task 22 status/generated task-file updates

Expected API response shape:

```python
{
    "items": [
        {
            "id": "...",
            "path": "...",
            "title": "...",
            "type": "...",
            "category": "...",
            "status": "...",
            "version": "...",
            "tags": [...],
            "dependencies": [...],
            "source": "...",
            "good_first_handler": False,
            "good_first_workflow": False,
            "metadata": {...},
        }
    ],
    "pagination": {
        "total": 1,
        "limit": 50,
        "offset": 0,
        "count": 1,
        "has_more": False,
    },
}
```

`get_template()` should return the serialized template record or `None`. `get_dependencies()` should return a serializable dependency payload for the requested template, including an empty list when the template has no dependencies.

## Acceptance Criteria

- Scope artifact exists and plan/tracker point at it.
- Taskmaster subtask `22.1` is marked done after plan sync.
- Tests prove:
  - serializable template lookup
  - query/category/status/version/tag filtering
  - deterministic pagination metadata
  - dependency extraction from frontmatter
  - missing-template behavior
- Final verification stores pytest, plan-sync, work-tracking audit, guard, and diff-check evidence under Task 22 reports.

## Progress Log

- **2026-05-08 18:10** — [S:20260508|W:task22-template-discovery-api|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/designs/template-discovery-api-scope-reconciliation.md] Reconciled Task 22 against the portable foundation and narrowed implementation to an in-process discovery facade.
