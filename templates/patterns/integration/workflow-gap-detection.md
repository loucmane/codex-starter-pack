---
id: workflow-gap-detection
type: pattern
category: integration
title: Workflow Gap Detection
pattern_type: routing
complexity: medium
dependencies:
  - templates/workflows/processes/meta-workflow-authoring.md
  - templates/handlers/orchestrators/meta-workflow-authoring.md
related:
  - patterns/meta-routing.md
version: 0.1.0
status: draft
---

# Workflow Gap Detection Pattern

## Pattern Description
Detects missing or outdated workflows/handlers/conventions and routes the request into the meta workflow authoring process before work begins.

## When to Use
- Guard reports "workflow not found" or "handler missing".
- Registry lookup fails to resolve an expected workflow asset.
- Migration plans reference monolithic entries lacking modular counterparts.
- Stakeholder explicitly requests a new workflow or major workflow revision.

## When NOT to Use
- Request is informational only (no workflow change required).
- Existing workflow already covers the requested scope (redirect to that workflow instead).

## Trigger Signals
1. Plan compliance guard flags missing workflow assets.
2. Session log references TODO/VOID handler for workflow execution.
3. Work-tracking backlog lists workflow migration debt.
4. Stakeholder asks for new workflow or significant change.

## Pattern Flow
1. Capture gap evidence in session + tracker (`S:W:H:E` entry).
2. Ensure plan compliance (active plan, scope recorded, sync log updated).
3. Route to `templates/handlers/orchestrators/meta-workflow-authoring.md` for execution.
4. Block further action until meta workflow authoring completes and guard passes.

## Evidence Requirements
- Session log entry referencing gap detection.
- Tracker progress note linking to plan scope.
- Guard output or registry search results showing the missing asset.
- Plan file with workflow deliverables enumerated.

## Expected Outputs
- Authored/updated workflow family (workflow, orchestrator, pattern, registry updates).
- Guard success log stored under `reports/<workflow-name>/`.
- Work-tracking + Serena memory documenting the change.

> Always consult the plan template before authoring workflows. If no plan exists, this pattern must abort and instruct the assistant to create one.
