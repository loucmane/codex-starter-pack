---
id: registry-index
title: Claude Template System Registry Index
type: registry-component
name: Claude Template System Registry Index
version: 3.0
status: modular
cross_references:
  - templates/registry/handlers/triggers-registry.md
  - templates/registry/handlers/orchestrators-registry.md
  - templates/registry/handlers/operators-registry.md
  - templates/registry/navigation/keywords.md
  - templates/registry/behavioral/templates.md
  - templates/patterns/routing/meta-routing.md
  - templates/registry/matrices/decision-matrices.md
---

# Claude Template System Registry - Modular v3.0

Lightweight entry point to the complete template system registry.

**Version**: 3.0 (Modularized)
**Structure**: Distributed across focused modules
**Discovery**: Both Read (direct) and Serena (search) supported

## 📚 Essential Documentation

- **New to Claude?** → [USER-GUIDE.md](../USER-GUIDE.md)
- **Common workflows?** → [templates/workflows/examples/common-workflows.md](../workflows/examples/common-workflows.md)
- **Creating handlers?** → [Creating and Managing Handlers](../integration/guides/creating-handlers.md#creating-and-managing-handlers)
- **Having issues?** → [USER-GUIDE.md#troubleshooting](../USER-GUIDE.md#troubleshooting-guide)

## 🎯 Registry Components

### Handler Registries (73+ handlers)
- **[Handler Index](../handlers/index.md)** - Canonical modular handler-family landing page and critical handler compatibility notes
- **[Triggers](handlers/triggers-registry.md)** - User-activated handlers (35)
- **[Orchestrators](handlers/orchestrators-registry.md)** - Coordination handlers (7)
- **[Operators](handlers/operators-registry.md)** - Technical operations (31)

### Navigation & Discovery
- **[Keywords](navigation/keywords.md)** - Natural language → handler mapping
- **[Behavioral Templates](behavioral/templates.md)** - Step-by-step guides (6)
- **[Meta-Routing](../patterns/routing/meta-routing.md)** - Ambiguous request handling (13)
- **[Compatibility Map](compatibility-map.json)** - Versioned legacy path redirects used by `TemplateRegistry.resolve()`
- **[Agent Compatibility Matrix](agent-compatibility-matrix.json)** - Versioned Codex/Claude/future-agent compatibility contract used by `codex-task agent compatibility-report`

### System Components
- **[Behavioral Hooks](behavioral/hooks.md)** - Automatic enforcement (9)
- **[Decision Matrices](matrices/decision-matrices.md)** - Quick lookups (5)
- **[Special Files](../conventions/files/special-files.md)** - File-specific rules

## 🧠 ULTRATHINK Resolution

**VOID State Resolution**: When H=VOID in ULTRATHINK format
1. Extract keywords from request
2. Check [Keywords](navigation/keywords.md) for mapping
3. Search handler registries if needed
4. Return valid handler ID or clarification request

**Quick Resolution**:
- S=VOID → [resolve-session-void](../handlers/orchestrators/resolve-session-void.md)
- W=VOID → [resolve-work-void](../handlers/operators/workflow/resolve-work-void.md)
- H=VOID → Search [Keywords](navigation/keywords.md) then registries

## Progress Log

- **2026-04-22 15:53** — [S:20260422|W:task91-standardize-template-metadata|H:templates/registry/index.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` metadata while keeping the registry index policy-exempt as an aggregate navigation entry
- **2026-05-11 19:04** — [S:20260511|W:task62-agent-compatibility-layer|H:templates/registry/index.md|E:templates/registry/agent-compatibility-matrix.json] Added the canonical agent compatibility matrix to the registry navigation
