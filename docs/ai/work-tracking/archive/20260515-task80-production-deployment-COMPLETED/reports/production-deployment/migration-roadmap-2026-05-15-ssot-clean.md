# Migration Roadmap

Generated: 2026-05-15T15:24:44.489591
Roadmap version: 1.0.0

## Summary Metrics

- **broken_reference_fixes**: 0
- **broken_references**: 0
- **checkpoints_saved**: 0
- **circular_dependencies**: 0
- **duplicate_count**: 4
- **duplicate_removals**: 2
- **exact_duplicate_groups**: 2
- **files_with_references**: 98
- **fully_migrated**: 4
- **migration_files_scanned**: 10
- **migration_percentage**: 37.5
- **modular_files**: 337
- **monolithic_files**: 8
- **not_migrated**: 1
- **orphaned_files**: 88
- **partial_duplicate_pairs**: 1
- **partially_migrated**: 5
- **pending_migration**: 6
- **recommendations**: 3
- **total_files**: 345
- **total_fixes**: 2
- **total_lines**: 56216
- **total_references**: 678
- **unique_references**: 303

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
| high | migration | L | medium | 10 | Complete migration work for templates/BEHAVIORS.md |
| high | migration | L | medium | 9 | Complete migration work for templates/HANDLERS.md |
| high | migration | L | medium | 10 | Complete migration work for templates/MATRICES.md |
| high | migration | L | medium | 10 | Complete migration work for templates/REGISTRY.md |
| high | migration | L | medium | 7 | Complete migration work for templates/TOOLS.md |
| medium | duplicates | S | low | 1 | Review duplicate command/template files kept by .claude/commands/tm/clear-subtasks/clear-all-subtasks.md |
| medium | duplicates | S | low | 1 | Review duplicate command/template files kept by .claude/commands/tm/clear-subtasks/clear-subtasks.md |
| low | orphaned-files | XL | high | 88 | Review 88 orphaned scanner files |

## Taskmaster Export Guidance

This roadmap contains 8 Taskmaster-compatible draft task entries. Review the JSON export before importing or creating tasks.

The generator does not mutate Taskmaster or apply fixes.
