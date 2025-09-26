
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

### Backlog: Meta Workflow Enforcement Follow-up (2025-09-25)
- **Task Proposal**: "Integrate meta workflow authoring enforcement"
  - Draft Taskmaster task covering orchestrator/pattern guard hooks, registry validation, Taskmaster alignment.
  - Subtasks:
    1. Wire meta workflow orchestrator + gap pattern into `codex-guard` (plan compliance + workflow-gap checks).
    2. Extend guard metadata (`templates/metadata/workflow-guards.json`) with workflow-gap triggers and validations.
    3. Update Taskmaster alignment checklist to require meta workflow plan before editing template assets.
    4. Document guard failure messaging and auto-fix guidance for missing meta workflow assets.
    5. Plan CI/pre-commit wiring for the new enforcement path (notes + TODO).
    6. Update `scripts/codex-task` helper to surface meta workflow requirements during scaffolding.
    7. Capture guard output + documentation references as evidence (reports + handoff).
- **Task Proposal**: "Meta workflow regression test suite"
  - Subtasks:
    1. Add unit tests confirming orchestrator/pattern registration via registries.
    2. Create integration test walking a sample workflow authoring cycle through the guard.
    3. Store test/guard reports under `reports/meta-workflow/` and reference in docs.
    4. Update testing documentation + CHANGELOG with coverage details.
    5. Plan CI integration (Taskmaster/Serena notes) for new tests.
  - Notes: add to Taskmaster only after review.

### Backlog: Plan Compliance Enforcement (Draft Extraction 2025-09-26)
- **Task Proposal**: "Implement plan compliance enforcement"
  - Subtasks:
    1. Finalize design scope (emergency bypass, amendments, continuation, conflict detection) and obtain sign-off.
    2. Implement `templates/behaviors/planning/plan-compliance.md` behavior with enforcement hooks.
    3. Extend `scripts/codex-guard` with mandatory plan structure & ID validation logic.
    4. Implement plan ↔ tracker sync validation (`.plan_state/sync.log` hash parity).
    5. Implement evidence verification (S:W:H:E + command proofs) before closing plan steps.
    6. Integrate guard hooks with session lifecycle & meta workflow authoring workflows.
    7. Document bypass/remediation guidance in work-tracking/HANDOFF.
    8. Capture guard/test evidence and Serena memory on completion.
  - Target placement: immediately after “Create Work-Tracking Template Structure” (Task 14).

### Backlog: Timestamp Validation Gate (Draft Extraction 2025-09-26)
- **Task Proposal**: "Implement timestamp guard"
  - Subtasks:
    1. Update `templates/behaviors/timestamps/before-adding.md` to enforce running `date "+%Y-%m-%d %H:%M %Z"` before logging timestamps.
    2. Extend `scripts/codex-guard` to detect recent date command output alongside timestamp entries.
    3. Update session/work-tracking templates with timestamp evidence checklist entries.
    4. Add helper guidance (codex-task message or alias suggestion) for capturing timestamps.
    5. Create regression tests ensuring guard fails on manual timestamps.
    6. Document guard usage and remediation steps in findings/handoff.
  - Target placement: after meta workflow enforcement tasks, before performance/security items.

### Backlog: Enforcement Framework Enhancements (Draft Extraction 2025-09-24)
- **Task Proposal**: "Expand enforcement framework"
  - Subtasks:
    1. Review enforcement framework draft and confirm scope (plan-first, guard-first, evidence-first).
    2. Identify gaps for new behaviors/guards (commit format enforcement, file scope guard, etc.) and stage future tasks.
    3. Update enforcement documentation to reference plan compliance + meta workflow guard requirements.
    4. Outline automation roadmap (CI, dashboard metrics, drift detection integration) for future phases.
    5. Coordinate enhancement backlog (wizard, metrics dashboard, drift detection) for prioritisation.
  - Notes: coordinating task to be inserted once plan compliance/meta workflow enforcement tasks land.

### Backlog: Session Continuation & State Management Workflows (Action 1)
- **Task Proposal**: "Author session continuation/state workflows"
  - Subtasks:
    1. Inventory existing session lifecycle references (compaction, continuation, state) and capture gaps.
    2. Author `templates/workflows/session/continuation.md` and `state-management.md` with full frontmatter.
    3. Update handlers/patterns/registry entries to route requests into the new workflows.
    4. Integrate guard checkpoints (session restoration, compaction recovery) with plan compliance workflow.
    5. Add S:W:H:E examples and documentation updates (TRACKER, HANDOFF, findings).
    6. Create regression tests ensuring guard/workflow hand-off behaves correctly across sessions.
  - Target placement: immediately before domain workflow modules.

### Backlog: Domain Workflow Packs (Action 3)
- **Task Proposal**: "Author domain workflow modules"
  - Subtasks:
    1. Inventory required domain categories (frontend, backend, API, testing, ops, documentation).
    2. Draft workflow files under `templates/workflows/domains/` with frontmatter + prerequisites.
    3. Map required conventions/guards for each domain and update enforcement hooks.
    4. Update registry/navigation to expose the new workflows.
    5. Provide sample S:W:H:E logs + codex-task helper prompts per domain.
    6. Run pilot executions (at least two domains) and capture findings/evidence.
  - Target placement: after session continuation/state workflows.

### Backlog: Legacy Anchor Remediation (Action 4)
- **Task Proposal**: "Replace monolithic references with modular paths"
  - Subtasks:
    1. Enumerate all references to WORKFLOWS.md, PATTERNS.md, CONVENTIONS.md, etc. (scanner + manual audit).
    2. Map each reference to its modular replacement; identify gaps requiring new modules.
    3. Implement replacements across templates/handlers/docs; capture diff evidence.
    4. Update guard to flag references to deprecated monolithic anchors.
    5. Document migration in findings/changelog with proof of replacement.
    6. Add regression test ensuring future references trigger guard.
  - Target placement: immediately after domain workflow packs.

### Backlog: Taskmaster Alignment Workflow (Action 5)
- **Task Proposal**: "Create Taskmaster alignment workflow"
  - Subtasks:
    1. Define prerequisites/checklist required before editing tasks.json (plan compliance, registry review, evidence capture).
    2. Author workflow/handler/pattern to enforce alignment steps within Taskmaster.
    3. Wire guard/CLI reminders so task edits require active plan + alignment checklist.
    4. Update documentation (tracker, handoff, codex-task helper) with alignment protocol.
    5. Create regression tests verifying CLI/guard block edits without alignment workflow.
  - Target placement: alongside legacy anchor remediation.

### Backlog: Work-Tracking Workflow Expansion (Action 6)
- **Task Proposal**: "Expand work-tracking orchestration"
  - Subtasks:
    1. Document the seven-file active folder plus related behavioural hooks (TodoWrite equivalents, Serena memories, compaction protocol).
    2. Author workflow/pattern enforcing work-tracking updates before/after implementation.
    3. Integrate guard signals ensuring tracker, implementation, findings, decisions are updated per templates.
    4. Provide helper automation (codex-task commands) for updating work-tracking docs.
    5. Capture regression evidence demonstrating workflow adherence across two sample sessions.
  - Target placement: before engine migration tasks.

### Backlog: Engine Migration Completion (Action 7)
- **Task Proposal**: "Complete engine Phase 2/3 migration"
  - Subtasks:
    1. Audit `templates/engine/` README for outstanding Phase 2/3 modules; create inventory.
    2. Author missing modules/workflows referenced in engine roadmap.
    3. Update registry/navigation to include new engine modules.
    4. Document tests/usage examples for each new engine module.
    5. Capture guard/automation hooks ensuring engine modules are discoverable.
  - Target placement: after work-tracking orchestration.

### Backlog: Metadata Standardization (Action 8)
- **Task Proposal**: "Standardize template metadata"
  - Subtasks:
    1. Inventory templates lacking status/type/version metadata.
    2. Define canonical metadata schema and publish guidance.
    3. Batch-update templates with missing metadata (include automated checks/scripts).
    4. Extend guard to require metadata presence on new/modified templates.
    5. Document the metadata rollout and regression evidence.
  - Target placement: after engine migration completion.

### Backlog: Workflow Guard Coverage Expansion (Action 9)
- **Task Proposal**: "Expand guard coverage"
  - Subtasks:
    1. Audit existing guard coverage to identify missing behavioural checks (commit format, scope, testing, etc.).
    2. Prioritize guard additions; schedule follow-on tasks where needed.
    3. Implement the highest-priority guards and integrate with codex-task helper messaging.
    4. Document guard updates and add regression tests.
    5. Capture evidence and update enforcement framework documentation.
  - Target placement: after metadata standardization.

### Backlog: Compaction Behavior Remediation (Action 10)
- **Task Proposal**: "Rewrite or retire compaction detection behavior"
  - Subtasks:
    1. Evaluate current compaction behavior usage and failure points.
    2. Decide on rewrite vs deprecation; draft new behaviour if required.
    3. Update workflow/handler references to new behavior (or remove obsolete references).
    4. Document new compaction protocol in work-tracking/HANDOFF.
    5. Add regression tests ensuring compaction checkpoints behave correctly.
  - Target placement: after guard coverage expansion.

### Backlog: Template Drift Detection Enhancement
- **Task Proposal**: "Implement template drift detection"
  - Subtasks:
    1. Finalize design from template-drift-detection-draft (scope, heuristics, output format).
    2. Implement drift detection script and integrate with codex-guard scanning.
    3. Store drift reports under reports/template-drift/ and document remediation workflow.
    4. Add regression tests verifying drift detection accuracy.
    5. Plan automation/CI integration for drift reports.
  - Target placement: enforcement enhancements phase.

### Backlog: Interactive Template Wizard Enhancement
- **Task Proposal**: "Build template wizard CLI"
  - Subtasks:
    1. Design wizard flow based on template-wizard-draft (inputs, prompts, outputs).
    2. Implement wizard CLI leveraging existing workflows/handlers.
    3. Integrate guard/checks to ensure wizard respects plan compliance and evidence requirements.
    4. Document usage, logging, and troubleshooting.
    5. Add regression tests covering common wizard paths.
  - Target placement: enforcement enhancements phase.

### Backlog: Template Metrics Dashboard Enhancement
- **Task Proposal**: "Create template metrics dashboard"
  - Subtasks:
    1. Define metrics schema (usage frequency, compliance rate, guard violations) from metrics-dashboard-draft.
    2. Build data collector parsing guard logs, plan sync logs, and task history.
    3. Implement dashboard/report (web or Markdown) summarizing metrics.
    4. Document maintenance process and alerting thresholds.
    5. Plan CI/cron integration for metrics refresh.
  - Target placement: enforcement enhancements phase.

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


### Enhancement Backlog (2025-09-24)
- Logged design drafts for template drift detection, interactive wizard, metrics dashboard.
- Backlog captured additional ideas (dependency graph, test harness, pre-commit hook, etc.).
- Prioritize high-value items after Phase 1 (plan compliance) implementation.
