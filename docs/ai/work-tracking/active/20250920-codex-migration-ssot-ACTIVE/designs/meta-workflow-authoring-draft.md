# Meta Workflow Authoring (Draft)

## Objective
Establish a repeatable protocol for adding or modifying workflows/handlers/conventions/guards so no gap enters the system without documentation, planning, and validation.

## Workflow Outline
1. **Gap Detection**
   - Triggered by plan compliance guard or routing pattern (`workflow-gap-detection`).
   - Requires ULTRATHINK execution and registry/inventory search.
   - Logs gap in sessions + tracker.
2. **Plan Compliance**
   - Ensure plan exists (see plan compliance draft) with `Confirm scope`, implementation, and verification steps.
   - Guard validation required before proceeding.
3. **Design Phase**
   - Identify assets to create/update (workflows, handlers, patterns, conventions, guard rules, documentation).
   - Update plan + tracker with specific deliverables.
   - Use sequential thinking if problem requires deeper reasoning.
4. **Scaffolding**
   - Create draft files under `plans/drafts/` or appropriate directories.
   - Include full frontmatter, references, evidence sections.
   - Update registry indexes and cross-references.
5. **Integration & Validation**
   - Run `codex-guard` (plan + session/work-tracking validation).
   - Execute relevant scanners/tests if workflow impacts code validation.
   - Ensure plan compliance (plan ↔ tracker sync) before marking implementation step complete.
6. **Documentation & Handoff**
   - Update sessions, tracker, implementation, findings, decisions, changelog, handoff.
   - Record Serena memory (checkpoint) describing the workflow change.
   - Prepare Taskmaster entry to reflect the new workflow.

## Update vs. Create
- **New workflow**: Follow full sequence above.
- **Modify existing workflow**:
  - Trigger plan compliance and guard checks.
  - Identify impacted assets (other workflows, handlers, plan template).
  - Update plan to include regression tests/validation for existing behavior.
  - Document rationale and risk assessment in findings/changelog.
  - Archive old workflow version if substantial changes are made.

## Dependencies & Touchpoints
- Plan compliance guard and behavior (must pass before edits).
- Registry (handler and pattern indexes) to list new orchestrator/pattern.
- Conventions/behaviors (update when workflow introduces new rules).
- Guard configuration (`codex-guard`) for enforcement.
- Work-tracking files (tracker checklists, plan file, session log, Serena memory).

## Tool Usage
- **Plan tool** (`update_plan`) – track steps, enforce discipline.
- **shell** (`rg`, `sed`, `python3`) – search/edit templates.
- **Serena** – code-aware searches/updates when modifying handler forests.
- **Taskmaster** – sync tasks once workflow accepted.
- **Sequential Thinking** – optional for complex design reasoning.

## Guard Preconditions
- Plan compliance guard (≥3 steps, scope confirmed).
- Plan ↔ tracker sync log updated (see plan compliance draft).
- Guard halts if plan content doesn’t match tracker or evidence is missing.

## Evidence Requirements
- Session + tracker entries with S:W:H:E for each step.
- Plan file and tracker checklist reflecting completed steps.
- Tests/guards run with output excerpted.
- Serena memory ID recorded in handoff.

## Open Questions
- Should meta workflow changes automatically update a central registry summary?
- How to manage multiple concurrent workflow changes? (suggest serializing via plan compliance guard).

## Next Steps
1. Review draft with loucmane.
2. Implement plan compliance behavior/guard first.
3. Author meta workflow files (workflow, orchestrator, pattern) following this draft.
4. Update templates/workflows and guard configuration accordingly.


## Plan Integration
- Step 0: run plan compliance guard; ensure plan-step IDs present and scope confirmed with loucmane.
- Plan must list every asset to be created/updated (files, registry entries, guard configs).

## Validation Suite
- Define required checks per change (e.g., codex-guard, scanners, tests).
- Plan must reference the exact commands to run; guard verifies evidence exists.

## Regression Requirements (Updates)
- When modifying existing workflows, plan includes regression validation (tests/guards) for previous behavior.
- Document expected behavior changes in Findings/Changelog.

## Rollback Guidance
- Plan contains rollback section: files to revert, commands to undo changes, guard to rerun.

## Documentation & Memory
- Handoff memory (Serena) must summarize new workflow and reference plan file.
- Tracker checklist includes meta workflow steps to ensure visibility.

## Multi-Step Coordination
- For concurrent workflow changes, plan must designate order or note isolation boundaries.
- Guard blocks overlapping workflow edits unless a shared plan path is approved.


## Execution Tasks (Draft)
- **TaskMASTER Task Proposal**
  - Task: "Implement meta workflow authoring"
    - Subtask 1: Finalize design draft
    - Subtask 2: Author workflow file (`templates/workflows/processes/meta-workflow-authoring.md`)
    - Subtask 3: Add orchestrator handler (`templates/handlers/orchestrators/meta-workflow-authoring.md`)
    - Subtask 4: Add gap-detection pattern (`templates/patterns/integration/workflow-gap-detection.md`)
    - Subtask 5: Update registry/conventions/docs/guard references
    - Subtask 6: Validate via guard/tests; record evidence
    - Subtask 7: Update plan/tracker/Serena handoff

> Note: Commit messages must use double quotes per templates/conventions/git/commit-format.md.
