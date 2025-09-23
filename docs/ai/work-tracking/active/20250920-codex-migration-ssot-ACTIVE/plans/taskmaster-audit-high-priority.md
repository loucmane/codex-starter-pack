# Taskmaster Audit – High Priority Corrections

## Objectives
- Ensure Taskmaster task graph aligns with actual template-system migration requirements.
- Identify missing or misplaced tasks covering workflow authoring, enforcement, and documentation.
- Prepare revisions to `tasks.json` before expanding remaining tasks.

## Key Findings (So Far)
- Task ordering mostly follows the migration phases but some items (Work-Tracking structure, cost tracking) need repositioning or clarification.
- Task 15 (Serena integration) corrected to focus on mandatory Serena usage.
- Missing dedicated effort for development workflows (frontend/backend/web/etc.) to route through template system.

## Proposed High-Priority Task Revisions
### New Task: Author Development Workflow Modules
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
