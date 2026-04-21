# Task 90 Engine Migration Roadmap Audit

## Objective
Identify the remaining engine modules, registries, and discoverability gaps that block completion of Phase 2/3 engine migration work.

## Audit Targets
- `templates/engine/`
- registry/index/navigation files that surface engine workflows
- archived Task 89 handoff and Taskmaster Task 90 definition
- any legacy monolith references that still point away from migrated engine modules

## Questions to Answer
1. Which engine modules are still missing or incomplete?
2. Which registry/navigation files need updates once modules are in place?
3. What tests or guard hooks already exist for engine module discoverability?
4. Which documentation surfaces need to reference the migrated engine modules?

## Initial Notes
- Task 90 begins immediately after the completed Task 89 enforcement lane.
- `task-master list` still suggests Task 1 in raw backlog order, but continuity for the completed 81-89 lane makes Task 90 the logical follow-up.
- The Task 89 active folder has been archived before opening this new Task 90 active folder, keeping a single active work-tracking folder in the repo.
- `templates/engine/README.md` is stale: it references multiple Phase 2/3 modules that do not exist on disk (`execution-engine.md`, `mode-detection.md`, trigger modules, `handler-validation.md`, `evidence-based.md`, `handler-loading.md`, `natural-execution.md`).
- Current discoverability sources (`templates/registry/index.json`, metadata inventory/summary) point at a different, newer set of engine files such as `core/session-resolver.md` and `validation/*`.
- Current `CLAUDE.md` no longer imports the engine module tree at all, which suggests Task 90 must first reconcile roadmap/docs/discoverability before deciding whether any missing modules should actually be authored.
- `templates/engine/verify-phase1.sh` is also stale: it still checks `.claude/templates/...` paths and old `CLAUDE.md` import comments that no longer exist in the current repo layout.

## Reconciliation Matrix
| Surface | Current State | Assessment |
|---------|---------------|------------|
| `templates/engine/README.md` | Lists many missing Phase 2/3 modules and an older module hierarchy | Stale roadmap / stale discoverability doc |
| `templates/engine/MODULARIZATION-COMPLETE.md` | Describes the newer extracted engine set and matches more of the current tree | Closer to canonical |
| `templates/registry/index.json` | Registers current engine files including `core/session-resolver.md` and `validation/*` | Current canonical discovery surface |
| `templates/metadata/*` | Inventory/summary/overview align with the newer current engine files | Current canonical discovery surface |
| `templates/engine/verify-phase1.sh` | Verifies old `.claude/templates/...` paths and import comments in `CLAUDE.md` | Stale verification artifact |
| `CLAUDE.md` | Only imports Taskmaster instructions now | No longer a consumer of engine module import comments |

## Scope Recommendation
Task 90 should begin by reconciling engine roadmap and discoverability documentation:
1. Update `templates/engine/README.md` to match the current engine file set.
2. Replace or modernize `templates/engine/verify-phase1.sh` so it validates current engine files rather than `.claude`-era paths.
3. Re-check whether any genuinely missing engine modules remain after documentation/verification drift is removed.

## Implementation Slice Result — 2026-04-21
- `templates/engine/README.md` has been rewritten to describe the current engine tree and the current discovery model.
- `templates/engine/verify-phase1.sh` now validates the actual engine files on disk, representative frontmatter-bearing modules, and key registry/metadata references.
- The verifier passes and the report is stored at `reports/complete-engine-migration/verify-phase1-2026-04-21-pass.txt`.
- The mixed `id`/`name` frontmatter convention is now treated as a real engine-tree invariant rather than a failure condition.
- Remaining audit question: do any engine-module or registry gaps remain once stale roadmap assumptions are removed?
