---
id: meta-workflow-authoring
name: Meta Workflow Authoring
title: Meta Workflow Authoring
role: orchestrator
type: orchestrator
domain: workflow
stability: draft
status: draft
triggers:
  - "create workflow"
  - "new workflow"
  - "missing workflow"
  - "workflow gap"
dependencies:
  - templates/workflows/processes/meta-workflow-authoring.md
  - templates/patterns/integration/workflow-gap-detection.md
  - templates/behaviors/planning/plan-compliance.md
  - templates/workflows/session/lifecycle.md
version: 0.1.0
---

#### Pattern: meta-workflow-authoring {#meta-workflow-authoring}
**Triggers**: Requests to create or repair workflows/handlers/conventions, or guard-detected workflow gaps.
**Pre-conditions**:
- ULTRATHINK complete with gap recorded in sessions/ and tracker.
- Active plan in `plans/current` using the standard plan template.

**Process**:
1. _Validate Plan_: Ensure plan compliance (scope confirmed with loucmane, plan ↔ tracker sync logged in `.plan_state/sync.log`).
2. _Design_: Capture requirements in `docs/ai/work-tracking/.../designs/`, identify affected templates/guards/registries.
3. _Scaffold_: Create or update workflow / handler / pattern files with full frontmatter and cross references.
4. _Integrate_: Update registry entries, metadata maps, and guard configuration; wire orchestrator + pattern into navigation.
5. _Validate_: Run `python3 scripts/codex-guard validate --include-untracked` and any domain tests/scanners; save outputs under `reports/<workflow-name>/`.
6. _Document_: Update work-tracking (TRACKER, IMPLEMENTATION, FINDINGS, DECISIONS, CHANGELOG, HANDOFF) and log Serena memory referencing plan + evidence.
7. _Handoff_: Archive plan (or bump version) and ensure Taskmaster entries reflect the new workflow responsibilities.

**Success**: New or updated workflow family (workflow, orchestrator, pattern, registry links) validated with guard/tests and fully documented.
**Failure**: Guard blocks due to missing plan, unsynced tracker, absent registries, or missing evidence.

**Examples**:
- “Create a workflow for onboarding new microservices” → routes through this orchestrator before authoring.
- Guard detects `templates/workflows/session/continuation.md` missing → orchestrator kicks off meta workflow authoring plan.

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/meta-workflow-authoring.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
