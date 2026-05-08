# Migration Roadmap

Generated: 2026-05-08T12:12:14.032335
Roadmap version: 1.0.0

## Summary Metrics

- **broken_reference_fixes**: 175
- **broken_references**: 175
- **checkpoints_saved**: 0
- **circular_dependencies**: 11
- **duplicate_count**: 4
- **duplicate_removals**: 2
- **exact_duplicate_groups**: 2
- **files_with_references**: 106
- **fully_migrated**: 4
- **migration_files_scanned**: 11
- **migration_percentage**: 37.5
- **modular_files**: 325
- **monolithic_files**: 8
- **not_migrated**: 2
- **orphaned_files**: 80
- **partial_duplicate_pairs**: 1
- **partially_migrated**: 5
- **pending_migration**: 7
- **recommendations**: 5
- **total_files**: 333
- **total_fixes**: 177
- **total_lines**: 56049
- **total_references**: 699
- **unique_references**: 425

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
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/file-operations/before-create.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/file-operations/before-edit.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/planning/plan-compliance.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/session/session-end.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/task-management/todo-write.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/work-tracking/update-tracker.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/conventions/docs/documentation-standards.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/coordination/session-swhe-integration.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/engine/navigation/common-flows.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/engine/validation/foundation-adoption-guide.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/integration/cross-system/tool-integration.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/integration/guides/extending-templates.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/patterns/integration/composition.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/patterns/integration/cross-system.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/MIGRATION-REPORT.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/handlers/operators-registry.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/handlers/orchestrators-registry.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/registry/handlers/triggers-registry.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/workflows/processes/meta-workflow-authoring.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/workflows/protocols/universal-flight.md |
| critical | references | L | high | 10 | Repair 10 broken references in templates/tools/index.md |
| critical | references | L | high | 12 | Repair 12 broken references in templates/HANDLERS.md |
| critical | references | L | high | 13 | Repair 13 broken references in templates/behaviors/index.md |
| critical | references | L | high | 13 | Repair 13 broken references in templates/guides/index.md |
| critical | references | L | high | 15 | Repair 15 broken references in templates/registry/index.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/BEHAVIORS.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/BUILDING-BETTER.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/WORKFLOWS.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/behaviors/session/compaction-detection.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/behaviors/validation/evidence-claims.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/conventions/docs/readme-format.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/architecture/handler-architecture.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/architecture/system-architecture.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/architecture/template-architecture.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/best-practices/handler-design.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/best-practices/integration-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/composition/handler-chaining.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/composition/pattern-composition.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/composition/workflow-composition.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/integration/cross-system/mcp-integration.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/evidence/evidence-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/evidence/proof-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/evidence/validation-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/routing/intent-detection.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/routing/meta-routing.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/routing/request-analysis.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/selection/agent-selection.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/selection/handler-selection.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/session/continuation-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/session/session-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/session/state-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/work-tracking/documentation-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/work-tracking/progress-patterns.md |
| critical | references | M | high | 2 | Repair 2 broken references in templates/patterns/work-tracking/work-patterns.md |
| critical | references | M | high | 3 | Repair 3 broken references in templates/handlers/tools/external/consult-gpt5.md |
| critical | references | M | high | 3 | Repair 3 broken references in templates/integration/best-practices/template-design.md |
| critical | references | M | high | 3 | Repair 3 broken references in templates/integration/guides/adding-agents.md |
| critical | references | M | high | 3 | Repair 3 broken references in templates/integration/guides/system-integration.md |
| critical | references | M | high | 3 | Repair 3 broken references in templates/patterns/selection/tool-selection.md |
| critical | references | M | high | 5 | Repair 5 broken references in templates/PROJECT-BLOG.md |
| critical | references | M | high | 5 | Repair 5 broken references in templates/integration/guides/creating-handlers.md |
| critical | references | L | high | 8 | Repair 8 broken references in templates/matrices/index.md |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 1 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 10 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 11 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 2 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 3 |
| high | dependencies | M | medium | 2 | Break circular dependency cycle 4 |
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
| medium | security | S | low | 1 | Review warning security finding in templates/PROJECT-BLOG.md |
| low | orphaned-files | XL | high | 80 | Review 80 orphaned scanner files |

## Taskmaster Export Guidance

This roadmap contains 83 Taskmaster-compatible draft task entries. Review the JSON export before importing or creating tasks.

The generator does not mutate Taskmaster or apply fixes.
