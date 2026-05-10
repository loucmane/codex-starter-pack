---
id: patterns-index
title: Pattern Templates Index
type: pattern-index
category: patterns
status: stable
version: 1.0.0
dependencies:
  - templates/patterns/templates/patterns/routing/meta-routing.md
  - templates/patterns/templates/patterns/selection/handler-selection.md
  - templates/patterns/templates/patterns/evidence/evidence-patterns.md
  - templates/patterns/templates/patterns/work-tracking/work-patterns.md
  - templates/patterns/templates/patterns/session/session-patterns.md
  - templates/patterns/templates/patterns/integration/composition.md
---

# Pattern Templates Index

Canonical index for modular pattern templates. Legacy top-level pattern-library references resolve here through `templates/registry/compatibility-map.json`.

## Routing

- [Meta-Routing Patterns](routing/meta-routing.md)
- [Request Analysis Patterns](routing/request-analysis.md)
- [Intent Detection Patterns](routing/intent-detection.md)

## Selection

- [Handler Selection Patterns](selection/handler-selection.md)
- [Tool Selection Patterns](../handlers/orchestrators/tool-selection.md)
- [Agent Selection Patterns](selection/agent-selection.md)

## Evidence

- [Evidence Collection Patterns](evidence/evidence-patterns.md)
- [Validation Patterns](evidence/validation-patterns.md)
- [Proof Requirement Patterns](evidence/proof-patterns.md)

## Work Tracking

- [Work Tracking Patterns](work-tracking/work-patterns.md)
- [Progress Measurement Patterns](work-tracking/progress-patterns.md)
- [Documentation Creation Patterns](work-tracking/documentation-patterns.md)

## Session

- [Session Management Patterns](session/session-patterns.md)
- [State Tracking Patterns](session/state-patterns.md)
- [Session Continuation Patterns](session/continuation-patterns.md)

## Integration

- [Cross-System Integration Patterns](integration/cross-system.md)
- [Pattern Composition Strategies](integration/composition.md)
- [Workflow Gap Detection](integration/workflow-gap-detection.md)

## Discovery Contract

- The top-level pattern-library document remains a legacy entrypoint.
- `templates/patterns/index.md` is the modular pattern-family landing page.
- Template registry compatibility lookup must redirect legacy pattern-library queries to this file and return a concrete registry record, not a bare directory.
- Pattern template metadata is governed by `templates/metadata/template-metadata-policy.json`.

## Progress Log

- **2026-05-09 15:48 CEST** — [S:20260509|W:task27-migrate-pattern-templates|H:templates/patterns/index.md|E:docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/designs/pattern-template-scope-reconciliation.md] Added the canonical modular pattern-family index so legacy pattern-library compatibility redirects resolve to a concrete registry record.
