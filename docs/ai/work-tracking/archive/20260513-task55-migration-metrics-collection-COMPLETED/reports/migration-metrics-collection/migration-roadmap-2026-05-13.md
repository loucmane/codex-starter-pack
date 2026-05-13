# Migration Roadmap

Generated: 2026-05-13T13:37:58.841972
Roadmap version: 1.0.0

## Summary Metrics

- **broken_reference_fixes**: 43
- **broken_references**: 43
- **checkpoints_saved**: 0
- **circular_dependencies**: 19
- **duplicate_count**: 4
- **duplicate_removals**: 2
- **exact_duplicate_groups**: 2
- **files_with_references**: 108
- **fully_migrated**: 4
- **migration_files_scanned**: 10
- **migration_percentage**: 37.5
- **modular_files**: 335
- **monolithic_files**: 8
- **not_migrated**: 1
- **orphaned_files**: 87
- **partial_duplicate_pairs**: 1
- **partially_migrated**: 5
- **pending_migration**: 6
- **recommendations**: 5
- **total_files**: 343
- **total_fixes**: 45
- **total_lines**: 55840
- **total_references**: 741
- **unique_references**: 327

## Phase Plan

| Phase | Priorities | Start Day | Duration |
|-------|------------|-----------|----------|
| Critical integrity | critical | 0 | 2 days |
| Foundation correctness | high | 2 | 3 days |
| Maintenance risk | medium | 5 | 2 days |
| Optimization backlog | low | 7 | 2 days |

## Prioritized Items

| Priority | Category | Effort | Risk | Findings | Title |
|----------|----------|--------|------|----------|-------|
| critical | references | S | high | 1 | Repair 1 broken reference in templates/MATRICES.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/REGISTRY.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/planning/plan-compliance.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/work-tracking/update-tracker.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/conventions/docs/documentation-standards.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/coordination/session-swhe-integration.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/engine/navigation/common-flows.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/engine/validation/foundation-adoption-guide.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/integration/best-practices/template-design.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/integration/guides/adding-agents.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/matrices/index.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/MIGRATION-REPORT.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/handlers/operators-registry.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/handlers/orchestrators-registry.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/handlers/triggers-registry.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/index.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/workflows/protocols/universal-flight.md |
| critical | references | L | high | 12 | Repair 12 broken references in templates/HANDLERS.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/BEHAVIORS.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/BUILDING-BETTER.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/WORKFLOWS.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/conventions/docs/readme-format.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/handlers/tools/external/consult-gpt5.md |
| critical | references | M | high | 4 | Repair 4 broken references in templates/integration/guides/creating-handlers.md |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 1 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 10 |
| high | dependencies | M | medium | 3 | Break circular dependency cycle 11 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 12 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 13 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 14 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 15 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 16 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 17 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 18 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 19 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 2 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 3 |
| high | dependencies | S | medium | 1 | Break circular dependency cycle 4 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 5 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 6 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 7 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 8 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 9 |
| high | migration | L | medium | 10 | Complete migration work for templates/BEHAVIORS.md |
| high | migration | L | medium | 8 | Complete migration work for templates/HANDLERS.md |
| high | migration | L | medium | 10 | Complete migration work for templates/MATRICES.md |
| high | migration | L | medium | 10 | Complete migration work for templates/REGISTRY.md |
| high | migration | L | medium | 7 | Complete migration work for templates/TOOLS.md |
| medium | duplicates | S | low | 1 | Review duplicate command/template files kept by .claude/commands/tm/clear-subtasks/clear-all-subtasks.md |
| medium | duplicates | S | low | 1 | Review duplicate command/template files kept by .claude/commands/tm/clear-subtasks/clear-subtasks.md |
| low | orphaned-files | XL | high | 87 | Review 87 orphaned scanner files |

## Taskmaster Export Guidance

This roadmap contains 51 Taskmaster-compatible draft task entries. Review the JSON export before importing or creating tasks.

The generator does not mutate Taskmaster or apply fixes.
