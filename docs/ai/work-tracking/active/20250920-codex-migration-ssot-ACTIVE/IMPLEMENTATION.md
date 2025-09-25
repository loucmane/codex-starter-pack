
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Implementation Plan

## Overview
Codex-first migration of the Claude template system. We need a clean Single Source of Truth that runs entirely inside this repository, including the SSOT scanner suite, modular templates, and Codex-specific enforcement docs.

## Approach
- Stand up the Codex work-tracking and session structure so changes stay compliant with the templates.
- Port the SSOT scanner tooling into this repo, align it with `.codex/`, and confirm the safety fixes described in the August work logs.
- Run the scanners locally, review outputs, and apply Codex-tailored fixes without re-introducing the dangerous scripts.
- Migrate remaining monolithic references into the modular folders once the tooling reports are clean.

## Steps
1. Scaffold work-tracking folder (`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE`) with the required seven files and supporting subdirectories (`plans/`, `designs/`, `code/`, `archive/`, `reports/`).
2. Spin up a new session log under `sessions/2025/09/` and link `sessions/current`.
3. Review historical safety notes (2025-08 work logs) to ensure we keep Serena tooling, safe reorganize scripts, and corrected reference fix scripts.
4. Copy the SSOT scanner suite into this repo, patch it for `.codex`, and rerun `scanner.py`, `analyze_references.py`, and follow-up scanners.
5. Triage scanner results: catalog broken references, circular dependencies, and migration status deltas.
6. Plan and apply modular template fixes (post-scanner) with `--dry-run` validation.
7. Document outcomes in FINDINGS/CHANGELOG and update TRACKER/HANDOFF.
8. Implement `codex-task` helper + diff-aware guard (see Plans section):
   - `scripts/codex-task` provides `sessions update`, `work-tracking update`, and `scanner run` subcommands that auto-scaffold S:W:H:E entries.
   - `scripts/codex-guard validate` inspects changed session/work-tracking files for handler/evidence compliance (supports `--include-untracked`).
   - Document usage in CODEX.md, AGENTS.md, and templates/TOOLS.md; keep optional pre-commit/CI wiring on the roadmap.
   - TODO: extend guard with auto-fix skeletons when safe (tracked in plans).
9. Produce enterprise-grade migration PRD (executive summary, RACI, dashboards, governance, scorecard) as input for Taskmaster planning.

## Success Criteria
- Work-tracking structure exists with populated files and subfolders.
- Sessions directory records today’s migration work with evidence links.
- SSOT scanner outputs live under `scripts/template-ssot-scanner/output/` for this repo and match the safety rules from the August analysis.
- Tooling documentation explicitly references Serena + Codex MCP usage.
- Enterprise migration PRD ready for Taskmaster parsing (80/300 task target).
- Ready list of remaining modularization tasks accompanied by clean scanner reports.
- `codex-task` helper + guard run cleanly (`codex-task …`, `codex-guard --validate`).


## Template System Audit Roadmap (2025-09-23)
The comprehensive template inventory surfaced ten remediation tracks. Each track will be executed sequentially after documenting scope in sessions/work-tracking and receiving stakeholder approval.

1. **Session Workflows (Action 1)** — Create `templates/workflows/session/continuation.md` and `state-management.md`, update handlers/patterns/registry, and replace legacy anchors.
2. **Meta Workflow Authoring (Action 2)** — Introduce workflow + orchestrator + guard to enforce creation protocol for new workflows/handlers.
3. **Domain Workflow Packs (Action 3)** — Author frontend/backend/API/testing/ops workflow modules, with matching conventions/guards/examples.
4. **Legacy Anchor Remediation (Action 4)** — Replace all `WORKFLOWS.md#…` references with modular equivalents or create the missing modules.
5. **Taskmaster Alignment (Action 5)** — Document pre-edit checklist workflow and integrate with `codex-task`/guard enforcement.
6. **Work-Tracking Orchestration (Action 6)** — Codify the seven-file active folder, TodoWrite integration, sessions, and Serena handoffs.
7. **Engine Migration Completion (Action 7)** — Finish Phase 2/3 modules listed in `templates/engine/README.md` and adjust documentation accordingly.
8. **Metadata Standardization (Action 8)** — Ensure every module frontmatter includes `type`, `status`, and related metadata.
9. **Workflow Guard Expansion (Action 9)** — Extend `templates/metadata/workflow-guards.json` to cover new workflows and Taskmaster enforcement.
10. **Compaction Behavior Cleanup (Action 10)** — Decide on archival/rewrite of deprecated `session/compaction-detection.md`.

All actions require recording scope in sessions/, tracker entries, and HANDOFF before modifying `tasks.json`.


### Upcoming Work: Meta Workflow Authoring (Action 2)
- Document formal process for creating/modifying workflows/handlers/conventions before implementation.
- Define scope for enforcing orchestrator + gap-detection pattern (implementation deferred).
- Capture dependency touchpoints (registry, behaviors, Taskmaster, Serena, TodoWrite) required once approved.
- Align outputs with guard updates (Action 9) and domain workflow packs (Action 3).


### Tooling Equivalence Notes
- Codex Plan tool functions as internal todo manager (Plan update = TodoWrite, Plan display = TodoRead).
- Work-tracking files capture detailed evidence; Taskmaster supplements when structured tasks needed.
- No separate Todo API; plan + tracker combo is the canonical method inside Codex.


### Plan Compliance Rules (Draft)
- Plan compliance behavior implemented; guard now validates plan template, tracker checklist, emergency bypass.
- Minimum plan structure: Scope confirmation → Implementation steps → Verification/reporting.
- Plan tool is mandatory before file edits; enforce via behavior + guard.
- Tracker checklist to mirror plan requirements (no plan, no work).
- Implementation pending review of behavior/template drafts.
- First Codex-native plan file (`plans/2025-09-25-plan-compliance-phase1.md`) active; `.plan_state/sync.log` hash recorded for guard parity.
- Guard passes with enhanced plan checks (`reports/plan-compliance-phase1/guard-20250925-2033.txt`); remain on plan-step-verify to complete documentation/test evidence.
- Guard passes with enhanced plan checks (`reports/plan-compliance-phase1/guard-20250925-2122.txt`); plan-step-verify completed after backlog/Serena memory updates.


### Meta Workflow Authoring (Draft)
- Workflow file added at `templates/workflows/processes/meta-workflow-authoring.md`; orchestrator/pattern now scaffolded (`templates/handlers/orchestrators/meta-workflow-authoring.md`, `templates/patterns/integration/workflow-gap-detection.md`).
- Registry updates in place (`templates/registry/handlers/orchestrators-registry.md`, `templates/registry/patterns/meta-routing.md`); guard verified with `--include-untracked` log.
- Logged new design drafts: drift detection, interactive wizard, metrics dashboard; backlog created for additional enhancements.
- Updated design drafts per Claude review (emergency bypass, plan amendments, CI integration, regression tasks).
- Drafts now include task/subtask outlines to convert into Taskmaster entries during implementation.
- Captured draft in `designs/meta-workflow-authoring-draft.md` (gap detection → plan → design → scaffolding → validation → documentation).
- Includes update vs. create differences, guard prerequisites, tool usage, and evidence expectations.
- Implementation pending plan compliance guard and stakeholder review.
