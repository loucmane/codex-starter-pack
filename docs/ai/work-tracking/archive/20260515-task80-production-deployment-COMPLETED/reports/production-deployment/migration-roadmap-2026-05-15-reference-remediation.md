# Migration Roadmap

Generated: 2026-05-15T14:52:57.843863
Roadmap version: 1.0.0

## Summary Metrics

- **broken_reference_fixes**: 0
- **broken_references**: 0
- **checkpoints_saved**: 0
- **circular_dependencies**: 19
- **duplicate_count**: 4
- **duplicate_removals**: 2
- **exact_duplicate_groups**: 2
- **files_with_references**: 104
- **fully_migrated**: 4
- **migration_files_scanned**: 10
- **migration_percentage**: 37.5
- **modular_files**: 337
- **monolithic_files**: 8
- **not_migrated**: 1
- **orphaned_files**: 87
- **partial_duplicate_pairs**: 1
- **partially_migrated**: 5
- **pending_migration**: 6
- **recommendations**: 4
- **total_files**: 345
- **total_fixes**: 2
- **total_lines**: 56172
- **total_references**: 747
- **unique_references**: 305

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

This roadmap contains 27 Taskmaster-compatible draft task entries. Review the JSON export before importing or creating tasks.

The generator does not mutate Taskmaster or apply fixes.
