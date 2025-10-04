---
id: domain-docs-workflow
type: workflow-component
category: domain
title: Documentation Domain Workflow
dependencies:
  - scripts/codex-guard
  - templates/handlers/operators/docs/check-docs-needed.md
related:
  - templates/handlers/operators/docs/validate-comments.md
version: 1.0.0
status: draft
---

# Documentation Domain Workflow

## Purpose
Ensure documentation changes follow conventions, capture guard evidence, and maintain knowledge consistency.

## Preconditions
- Documentation scope defined in plan/tracker
- Style guide available (templates/conventions/docs/*)

## Steps
1. **Assess Documentation Needs**
   - Run `codex-task docs check-docs-needed` if available
   - Identify files to update
2. **Author / Update Docs**
   - Apply style/structure from docs conventions
   - Record progress in tracker
3. **Validation**
   - Run linters or doc build tools if applicable
   - Execute guard (`python3 scripts/codex-guard validate --include-untracked`)
4. **Evidence**
   - Store guard log under `reports/documentation/`
   - Update findings/decisions for doc changes
5. **Handoff**
   - Summarize doc updates in session log
   - Provide follow-up notes in handoff

## Evidence Requirements
- Guard log referencing doc updates
- Tracker/session entries describing documentation changes
- Optional: build logs for doc generation

## Failure Modes & Recovery
- **Style violations** → consult docs conventions, rerun guard
- **Missing updates** → use doc mapping to ensure completeness

## Completion Criteria
- Guard passes with doc evidence stored
- Tracker/session reflect documentation status
