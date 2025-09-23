
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Taskmaster Audit – High Priority Corrections

## Objectives
- Ensure Taskmaster task graph aligns with actual template-system migration requirements.
- Identify missing or misplaced tasks covering workflow authoring, enforcement, and documentation.
- Prepare revisions to `tasks.json` before expanding remaining tasks.

## Key Findings (So Far)
- Task ordering mostly follows the migration phases but some items (Work-Tracking structure, cost tracking) need repositioning or clarification.
- Task 15 (Serena integration) corrected to focus on mandatory Serena usage.
- Missing dedicated effort for development workflows (frontend/backend/web/etc.) to route through template system.
- Full template audit surfaced additional gaps: missing session continuation/state workflows, lack of meta workflow authoring process, absent domain workflow packs, lingering WORKFLOWS.md anchors, no Taskmaster-alignment workflow, incomplete work-tracking orchestration, unfinished engine Phase 2/3 modules, inconsistent metadata, limited guard coverage, and deprecated compaction-detection behavior.

## Proposed High-Priority Task Revisions
### New Task: Author Development Workflow Modules (status: pending review)
- **Purpose**: Create and enforce standardized workflows for frontend/backend/web/API/testing/ops within the template system.
- **Subtasks (draft)**:
  1. Inventory required workflow categories and existing handlers.
  2. Design workflow templates in `templates/workflows/` for each category.
  3. Document handler chains and enforcement rules per workflow.
  4. Update `codex-task` to require workflow selection before edits.
  5. Configure guard checks to validate workflow-specific conventions.
  6. Integrate workflows into work-tracking (session templates, tracker, handoff).
  7. Produce example S:W:H:E logs demonstrating workflow execution.
  8. Validate by running a full workflow (frontend/backend) through template system.

### Additional Adjustments
- Clarify Task 14 (Work-Tracking Template Structure) subtasks to cover more than the seven canonical files (execution engine, enforcement hooks, reporting).
- Reposition Task 24 (Cost Tracking) later alongside telemetry/metrics tasks.
- Ensure Task 18 (Security Validation) precedes Task 50 (Security Audit Process).

## Next Steps
- Insert “Author Development Workflow Modules” task around Task 14–15 in `tasks.json`.
- Refine Task 14 subtasks to cover extended work-tracking engine.
- Adjust task ordering and dependencies accordingly.
- Review tasks 16+ for similar misalignments.

## Execution Notes
- 2025-09-22: Inserted Task 15 "Author Development Workflow Modules" ahead of Serena enforcement and renumbered downstream tasks. Pending review of subtasks for Tasks 16+.
- Document recommended actions from template audit (Action 1–10)

## Recommended Actions Tracking
- Action 1 (session workflows): READY – documenting scope before implementation
- Action 2 (meta workflow authoring): drafting plan before implementation (workflow, orchestrator, gap-pattern to follow)
- Action 3 (domain workflow packs): queued
- Action 4 (replace legacy anchors): queued
- Action 5 (Taskmaster alignment workflow): queued
- Action 6 (work-tracking workflow expansion): queued
- Action 7 (engine migration completion): queued
- Action 8 (metadata standardization): queued
- Action 9 (workflow guard coverage): queued
- Action 10 (compaction detection behavior): queued


### Action 2 Scope (Meta Workflow Authoring)
- Create `templates/workflows/processes/meta-workflow-authoring.md` detailing the end-to-end protocol for introducing new workflows/handlers/conventions/guards.
- Add orchestrator `templates/handlers/orchestrators/meta-workflow-authoring.md` to enforce the process.
- Add pattern `templates/patterns/integration/workflow-gap-detection.md` to route unresolved requests.
- Update registry, conventions, behaviors, Taskmaster plan, and documentation hubs to reference the new workflow.
- Defer guard automation wiring to Action 9; document required hooks now.


### Plan Tool Equivalence
- Codex Plan = Claude Todo List (Plan update = TodoWrite, Plan display = TodoRead).
- Use plan checklists alongside TRACKER.md to capture subtask status within Codex environment.


### Plan Compliance Draft
- Requirement: Every plan must include ≥3 steps (scope confirmation, implementation, verification) before edits.
- Guard Hook: `codex-guard` will fail if plan entries missing or incomplete.
- Checklist: Tracker to include plan compliance items for each action.
- Drafting new behavior (`templates/behaviors/planning/plan-compliance.md`) + plan template (no implementation yet).


### Session Wrap (2025-09-23)
- Documented plan compliance, meta workflow, and timestamp gate designs (with execution tasks).
- No implementation performed; all changes are draft documentation and task outlines.
- Next session: review drafts, approve guard/behavior scope, then implement plan compliance first.
