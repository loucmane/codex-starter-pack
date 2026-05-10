---
id: handlers-index
title: Handler Templates Index
type: handler-index
category: handlers
status: stable
version: 1.0.0
dependencies:
  - templates/registry/handlers/triggers-registry.md
  - templates/registry/handlers/orchestrators-registry.md
  - templates/registry/handlers/operators-registry.md
  - templates/handlers/templates/handlers/triggers/development/start-new-work.md
  - templates/handlers/templates/handlers/triggers/debug/fix-bug.md
  - templates/handlers/templates/handlers/triggers/test/create-test-checkpoint.md
---

# Handler Templates Index

Canonical index for modular handler templates. Legacy top-level handler-library references resolve here through `templates/registry/compatibility-map.json`.

## Handler Families

- [Trigger Handlers](../registry/handlers/triggers-registry.md)
- [Orchestrator Handlers](../registry/handlers/orchestrators-registry.md)
- [Operator Handlers](../registry/handlers/operators-registry.md)

## Critical Handler Compatibility

| Legacy or user-facing name | Canonical handler | Location |
|----------------------------|-------------------|----------|
| `start-new-work` | `start-new-work` | [templates/handlers/triggers/development/start-new-work.md](triggers/development/start-new-work.md) |
| `fix-problem` | `fix-bug` | [templates/handlers/triggers/debug/fix-bug.md](triggers/debug/fix-bug.md) |
| `fix-bug` | `fix-bug` | [templates/handlers/triggers/debug/fix-bug.md](triggers/debug/fix-bug.md) |
| `test-implementation` | `create-test-checkpoint` | [templates/handlers/triggers/test/create-test-checkpoint.md](triggers/test/create-test-checkpoint.md) |
| `create-test-checkpoint` | `create-test-checkpoint` | [templates/handlers/triggers/test/create-test-checkpoint.md](triggers/test/create-test-checkpoint.md) |
| `validate-changes` | `validate-changes` | [templates/handlers/triggers/test/validate-changes.md](triggers/test/validate-changes.md) |

## Discovery Contract

- The top-level `templates/HANDLERS.md` file remains a legacy entrypoint.
- `templates/handlers/index.md` is the modular handler-family landing page.
- `TemplateRegistry.resolve("templates/HANDLERS.md")` must redirect to this file and return a concrete registry record.
- `TemplateRegistry.resolve("<handler-id>")` must load critical handlers through frontmatter IDs or explicit compatibility aliases.
- Handler template metadata is governed by `templates/metadata/template-metadata-policy.json`.

## Progress Log

- **2026-05-10 14:35 CEST** — [S:20260510|W:task26-critical-handler-templates|H:templates/handlers/index.md|E:docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/designs/critical-handler-templates-scope-reconciliation.md] Added the canonical modular handler-family index so legacy handler-library compatibility redirects resolve to a concrete registry record.
