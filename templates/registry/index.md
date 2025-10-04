---
id: registry-index
type: registry-component
name: Claude Template System Registry Index
version: 3.0
status: modular
cross_references:
  - handlers/triggers-registry.md
  - handlers/orchestrators-registry.md
  - handlers/operators-registry.md
  - navigation/keywords.md
  - behavioral/templates.md
  - patterns/meta-routing.md
  - matrices/decision-matrices.md
---

# Claude Template System Registry - Modular v3.0

Lightweight entry point to the complete template system registry.

**Version**: 3.0 (Modularized)
**Structure**: Distributed across focused modules
**Discovery**: Both Read (direct) and Serena (search) supported

## 📚 Essential Documentation

- **New to Claude?** → [USER-GUIDE.md](../templates/USER-GUIDE.md)
- **Common workflows?** → [templates/workflows/examples/common-workflows.md](../templates/workflows/examples/common-workflows.md)
- **Creating handlers?** → [BUILDING-BETTER.md#creating-handlers](../templates/integration/#creating-handlers)
- **Having issues?** → [USER-GUIDE.md#troubleshooting](../templates/USER-GUIDE.md#troubleshooting-guide)

## 🎯 Registry Components

### Handler Registries (73+ handlers)
- **[Triggers](handlers/triggers-registry.md)** - User-activated handlers (35)
- **[Orchestrators](handlers/orchestrators-registry.md)** - Coordination handlers (7)
- **[Operators](handlers/operators-registry.md)** - Technical operations (31)

### Navigation & Discovery
- **[Keywords](navigation/keywords.md)** - Natural language → handler mapping
- **[Behavioral Templates](behavioral/templates.md)** - Step-by-step guides (6)
- **[Meta-Routing](patterns/meta-routing.md)** - Ambiguous request handling (13)

### System Components
- **[Behavioral Hooks](behavioral/hooks.md)** - Automatic enforcement (9)
- **[Decision Matrices](matrices/decision-matrices.md)** - Quick lookups (5)
- **[Special Files](conventions/special-files.md)** - File-specific rules

## 🧠 ULTRATHINK Resolution

**VOID State Resolution**: When H=VOID in ULTRATHINK format
1. Extract keywords from request
2. Check [Keywords](navigation/keywords.md) for mapping
3. Search handler registries if needed
4. Return valid handler ID or clarification request

**Quick Resolution**:
- S=VOID → [resolve-session-void](../templates/handlers/orchestrators/resolve-session-void.md)
- W=VOID → [resolve-work-void](../templates/handlers/operators/workflow/resolve-work-void.md)
- H=VOID → Search [Keywords](navigation/keywords.md) then registries