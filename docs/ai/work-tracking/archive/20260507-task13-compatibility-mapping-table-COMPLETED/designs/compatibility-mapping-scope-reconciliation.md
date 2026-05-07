# Compatibility Mapping Scope Reconciliation

**Captured**: 2026-05-07 15:49 CEST
**Task**: 13 - Implement Compatibility Mapping Table

## Historical Task Wording

Task 13 originally asks for a `CompatibilityMap` class with bidirectional mapping, JSON storage, O(1) lookups, version tracking, incremental updates, conflict resolution, and validation.

## Current Repository Evidence

The current repository already has runtime compatibility behavior in `scripts/template_registry.py`:

- `TemplateRegistry.resolve()` checks modular registry ids first.
- Legacy monolith paths can redirect through `DEFAULT_COMPATIBILITY_MAP`.
- Existing tests cover fallback order: modular registry, compatibility redirect, legacy file, Serena fallback, and error.

The missing piece is that compatibility data is hardcoded in Python rather than maintained as a durable, versioned registry table.

## Proven Gap

Task 13 should not build a separate compatibility subsystem. The current-state gap is:

- make the existing compatibility mapping table durable and versioned;
- add bidirectional lookup semantics in the registry module;
- validate duplicate/conflicting mapping entries deterministically;
- validate current targets exist;
- keep existing `TemplateRegistry.resolve()` behavior unchanged for callers.

## Decision

Implement:

- `templates/registry/compatibility-map.json`
- `CompatibilityEntry`
- `CompatibilityMap`
- `CompatibilityMapError`
- registry loading from the JSON file, with constructor mapping fallback for tests/cross-project compatibility

Do not introduce a separate database, migration command, or scanner output format in Task 13. This is a registry-runtime data hardening task.

## Acceptance

Task 13 is complete when:

- real legacy paths still redirect through `TemplateRegistry.resolve()`;
- compatibility map targets validate with no missing paths;
- tests prove JSON-backed compatibility lookup, bidirectional lookup, conflict rejection, and existing fallback order;
- Taskmaster Task 13 and subtasks 13.1/13.2 are done;
- plan sync, work-tracking audit, guard, and diff-check pass.

