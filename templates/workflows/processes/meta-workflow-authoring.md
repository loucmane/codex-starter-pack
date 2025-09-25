---
id: meta-workflow-authoring
type: workflow
category: processes
title: Meta Workflow Authoring
version: 0.1.0
status: draft
dependencies:
  - templates/behaviors/planning/plan-compliance.md
  - templates/workflows/processes/plan-template.md
  - templates/metadata/workflow-guards.json
related:
  - templates/handlers/orchestrators/meta-workflow-authoring.md
  - templates/patterns/integration/workflow-gap-detection.md
---

# Meta Workflow Authoring

Author or update workflows, handlers, conventions, and guards through a structured, evidence-backed process. This workflow prevents gaps by forcing plan-first execution, registry updates, and guard validation before any template change lands.

## Preconditions
- ULTRATHINK protocol completed and relevant registry entries reviewed.
- Active plan exists via `plans/current` following the [Standard Plan Template](plan-template.md) with scope confirmed by loucmane.
- `scripts/codex-guard validate` passes for existing changes (or blockers are documented in plan + tracker).

## Required Inputs
- Session log with S:W:H:E entries referencing this workflow.
- Work-tracking tracker checklist row for the current meta authoring effort.
- Existing design notes (if applicable) stored under `docs/ai/work-tracking/.../designs/`.

## Workflow Table
| Step | Action | Evidence |
|------|--------|----------|
| 1 | Detect & log gap using registry inventory, update sessions + tracker | Session entry `[S|W|H|E]`, tracker gap note |
| 2 | Validate plan compliance (scope, deliverables, verification) | `plans/current`, tracker checklist, `.plan_state/sync.log` |
| 3 | Design assets (workflows/handlers/patterns/guards) and capture in design docs | Updated design files, plan amendments |
| 4 | Scaffold artefacts with full frontmatter and cross-references | New/updated template files, registry updates |
| 5 | Integrate & validate via guard/tests/scanners | Guard output, test logs, scanner reports |
| 6 | Document results, update work-tracking, create Serena memory, prep Taskmaster entries | Tracker/Implementation/Handoff updates, memory ID |

## Execution Steps
1. **Gap Detection**
   - Run inventory/registry search to confirm asset absence or mismatch.
   - Record discovery in session log (`S:W:H:E` entry) and tracker progress log.
   - Add preliminary scope to the active plan.

2. **Plan Compliance**
   - Ensure plan contains `plan-step-scope`, `plan-step-implement`, `plan-step-verify` with concrete deliverables.
   - Sync plan ↔ tracker (`.plan_state/sync.log`) before editing files.
   - Guard must acknowledge plan compliance before moving forward.

3. **Design Phase**
   - Capture design rationale, dependencies, and regression expectations in `designs/`.
   - Use sequential thinking (Serena/TodoRead equivalents) when deeper reasoning is required.
   - Update plan with any amendments and increment version if scope changes.

4. **Scaffolding**
   - Create or modify workflow/handler/pattern files with complete frontmatter (id, type, status, dependencies).
   - Update registry indexes, metadata, and guard mappings so assets can be discovered automatically.
   - Maintain draft copies under `plans/drafts/` or `designs/` if awaiting approval.

5. **Integration & Validation**
   - Run `python3 scripts/codex-guard validate` (include `--include-untracked` when drafting new files).
   - Execute relevant scanners/tests (SSOT suite, lint, unit tests) when changes impact execution paths.
   - Record outputs under `reports/<workflow-name>/` and link them in the plan evidence column.

6. **Documentation & Handoff**
   - Update work-tracking (`TRACKER.md`, `IMPLEMENTATION.md`, `FINDINGS.md`, `DECISIONS.md`, `CHANGELOG.md`, `HANDOFF.md`).
   - Create or append Serena memory summarizing changes and evidence.
   - Prepare Taskmaster tasks/subtasks reflecting newly introduced workflow responsibilities.

## Completion Criteria
- Plan step statuses set to `completed`, with evidence recorded and synced.
- Guard, tests, and scanners pass with outputs stored in `reports/`.
- Registries/metadata updated; no broken references remain.
- Work-tracking and session logs contain final S:W:H:E entries.
- Serena memory ID recorded in HANDOFF.

## Rollback Guidance
- If validation fails, revert modified files using git and restore archived plan version (`plans/archive/`).
- Document rollback details in Findings and update plan with follow-up actions.

## Future Enhancements
- Add orchestrator handler and gap-detection pattern (see related references) for automatic routing.
- Integrate Taskmaster alignment workflow to auto-suggest tasks after completion.
- Extend guard with conflict detection for concurrent workflow changes.

> Always run this workflow under an active plan. If an emergency bypass is required, document the waiver, create a post-mortem plan within 24 hours, and reference it in the tracker and Serena memory.
