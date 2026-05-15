---
id: orchestrators-registry
title: Orchestrator Handlers Registry
type: registry-component
name: Orchestrator Handlers Registry
description: Complete registry of coordination and orchestration handlers
status: stable
handler_count: 8
cross_references:
  - ../index.md
  - triggers-registry.md
  - operators-registry.md
---

# Orchestrator Handlers Registry

Coordination handlers that manage complex workflows and multi-handler operations.

## Workflow Orchestration (3 handlers)

### `standard-dev-workflow` {#standard-dev-workflow}
- **Triggers**: "implement X", "add feature Y", "create functionality Z"
- **Keywords**: [implement, feature, functionality, develop, add, create]
- **Process**: Full development workflow with research, implementation, testing
- **Location**: handlers/orchestrators/standard-dev-workflow.md

### `orchestrate-complex` {#orchestrate-complex}
- **Triggers**: "this needs multiple experts", "orchestrate X", "coordinate specialists"
- **Keywords**: [orchestrate, coordinate, multiple, experts, complex]
- **Process**: Coordinates multiple specialists for complex tasks
- **Location**: handlers/orchestrators/orchestrate-complex.md

### `session-start` {#session-start}
- **Triggers**: Starting a new session (automatic)
- **Keywords**: [session, initialization, setup, context]
- **Process**: Initializes session context and workspace
- **Location**: handlers/orchestrators/session-start.md

## VOID Resolution (1 handler)

### `resolve-session-void` {#resolve-session-void}
- **Triggers**: S=VOID in ULTRATHINK format
- **Keywords**: [session, void, resolve, missing]
- **Process**: Resolves missing session ID from sessions/
- **Location**: handlers/orchestrators/resolve-session-void.md

## Convention Enforcement (2 handlers)

### `check-conventions-first` {#check-conventions-first}
- **Triggers**: Internal trigger before actions
- **Keywords**: [check, conventions, first, before]
- **Process**: Mandatory convention check before operations
- **Location**: handlers/orchestrators/check-conventions-first.md

### `enforce-pre-flight` {#enforce-pre-flight}
- **Triggers**: "enforce conventions", "make sure I check"
- **Keywords**: [enforce, preflight, check, ensure]
- **Process**: System-wide enforcement of conventions
- **Location**: handlers/orchestrators/enforce-pre-flight.md

## Meta Coordination (2 handlers)

### `meta-orchestration` {#meta-orchestration}
- **Triggers**: Complex requests requiring multiple orchestrators
- **Keywords**: [meta, complex, multi-phase, pipeline]
- **Process**: Coordinates other orchestrators for very complex tasks
- **Location**: handlers/orchestrators/meta-orchestration.md

### `meta-workflow-authoring` {#meta-workflow-authoring}
- **Triggers**: "create workflow", "new workflow", guard-detected workflow gaps
- **Keywords**: [workflow, authoring, meta, gap]
- **Process**: Enforces plan-first workflow creation (plan compliance, design docs, scaffolding, validation, documentation)
- **Location**: handlers/orchestrators/meta-workflow-authoring.md

## Key Characteristics

**Orchestrators vs Triggers**:
- Orchestrators coordinate multiple handlers
- Triggers typically perform single focused tasks
- Orchestrators manage state across operations
- Orchestrators handle complex multi-step workflows

**When to Use Orchestrators**:
1. Task requires multiple domain experts
2. Need to coordinate between different systems
3. Complex state management across operations
4. Multi-phase workflows with dependencies

**Common Orchestration Patterns**:
1. **Sequential**: Step A → Step B → Step C
2. **Parallel**: Run A, B, C simultaneously
3. **Conditional**: If A succeeds, do B; else do C
4. **Iterative**: Repeat until condition met

**Discovery Methods**:
- Direct Read: use the concrete orchestrator file under `templates/handlers/orchestrators/`.
- Serena Search: `--substring_pattern "id: [handler-name]" --relative_path "templates/handlers/orchestrators/"`

## Progress Log

- **2026-04-22 15:53** — [S:20260422|W:task91-standardize-template-metadata|H:templates/registry/handlers/orchestrators-registry.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 registry-family standardization slice
