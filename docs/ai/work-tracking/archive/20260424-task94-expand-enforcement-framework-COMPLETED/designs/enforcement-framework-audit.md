# Task 94 Enforcement Framework Audit

## Purpose

Task 94 turns the older enforcement framework draft into the current sequenced roadmap that the repo can actually execute. The draft predates Tasks 93-102, so the goal is not to re-open already completed guard work. The goal is to align the framework narrative with the now-real backlog.

## Sources Reviewed

- `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/enforcement-framework-draft.md`
- `docs/ai/work-tracking/archive/20260421-task91-standardize-template-metadata-COMPLETED/designs/foundation-portability-roadmap.md`
- Taskmaster Tasks `94` through `102`

## Current Reality vs Draft

### Already Completed Since The Original Draft

The older draft listed several enforcement foundations as future work that are now complete:

- plan compliance guard and workflow
- timestamp gate
- session continuation and session-state enforcement
- work-tracking enforcement
- metadata standardization
- expanded workflow guard coverage
- compaction cleanup

Task 94 should therefore avoid re-planning those completed layers.

### What The Draft Still Gets Right

The draft still correctly identifies the next enforcement themes:

1. drift detection
2. interactive workflow or wizard support
3. metrics or dashboard visibility
4. stronger portability beyond this repo's hardcoded structure

Those themes now exist as the concrete Taskmaster chain `95` through `102`.

## Sequenced Roadmap

### Task 94 - Framework Alignment

Task 94 is a documentation-and-sequencing bridge. Its deliverables are:

- confirm the enforcement framework narrative after Task 93
- clarify which enhancements are generic framework work versus repo-portability work
- verify that backlog sequencing still makes sense
- document the automation roadmap for the next tasks

### Task 95 - Drift Detection

First concrete enhancement after Task 94.

Reason: drift detection strengthens the guard/reporting foundation and gives later tasks better observability. It is a natural first implementation because it builds on the guard/report infrastructure already in place.

### Task 96 - Interactive Template Wizard

Can proceed after Task 94 in parallel with or after Task 95.

Reason: the wizard depends on a stable enforcement framework definition, but does not need to wait for portability work. It should consume guard rules rather than redefining them.

### Task 97 - Metrics Dashboard

Follows Tasks 94, 95, and 96.

Reason: metrics become more useful after drift detection and wizard telemetry points are defined. The dashboard should summarize the health of the existing enforcement system rather than inventing new enforcement semantics.

### Tasks 98-102 - Portability Foundation

These are a distinct second phase:

- `98` externalize repo structure configuration
- `99` define portable foundation specification
- `100` build bootstrap layer
- `101` add cross-project compatibility fixtures
- `102` document migration and adoption

Reason: this phase makes the foundation reusable across future repos. It should not be mixed into Task 94 because portability work depends on a coherent enforcement framework and dashboard-level understanding of the current system first.

## Implementation Boundary

Task 94 should stay out of direct feature implementation for:

- drift-check commands
- wizard CLI behavior
- metrics collectors or dashboard code
- repo-shape externalization

Those belong to Tasks 95-102.

Task 94 should focus on:

- framework narrative
- sequencing decisions
- documentation updates
- backlog coordination

## Automation Roadmap

The next automation layers should build in this order:

1. **Guard and report enhancement** via drift detection (`95`)
2. **Guided operator workflow** via wizard support (`96`)
3. **Visibility and reporting layer** via metrics dashboard (`97`)
4. **Repo-portable configuration, spec, bootstrap, and adoption** via `98`-`102`

This keeps the system incremental:

- first detect drift
- then improve guided usage
- then measure it
- then make it portable

## Backlog Coordination Notes

- Task dependencies `94 -> 95/96 -> 97 -> 98 -> 99 -> 100 -> 101 -> 102` are coherent and do not need changes.
- Tasks `98` through `102` have no subtasks yet; they should be expanded before implementation starts.
- No new Taskmaster tasks are required right now; the needed work is already represented.

## Outcome

Task 94 can complete once the framework documentation and work-tracking artifacts record:

- the updated framework story
- the sequencing rationale for Tasks `95` through `102`
- the automation roadmap
- confirmation that backlog coordination is already represented in Taskmaster
