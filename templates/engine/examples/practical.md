---
id: practical-examples
title: Practical Examples
type: engine-component
status: stable
dependencies:
  - engine/navigation/template-protocol
  - engine/structure/template-system
  - shared/patterns/ultrathink
  - templates/REGISTRY
  - templates/WORKFLOWS
  - templates/TOOLS
  - templates/BEHAVIORS
exports:
  - example-implement-feature
  - example-debug-issue
  - example-natural-conversation
  - example-session-update
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Practical Examples

## User: "implement user authentication"
```
My Internal Process:
1. [DETECT] "implement" → Development signal
2. [SEARCH] REGISTRY for "implement" → Find "implement-feature"
3. [LOAD] Handler from templates/workflows/
4. [CHECK] Tool matrix for correct tools
5. [CREATE] Work folder 20250715-user-auth-ACTIVE/
6. [INIT] TodoWrite with implementation tasks
7. [EXECUTE] Follow TDD workflow from handler
```

## User: "why is the login failing?"
```
My Internal Process:
1. [DETECT] "why is" + "failing" → Debug signal
2. [SEARCH] REGISTRY for "debug" → Find debug handler
3. [LOAD] Handler from TOOLS.md
4. [GATHER] Evidence with Serena searches
5. [ANALYZE] With loaded debug workflow
6. [RESPOND] With evidence-based findings
```

## User: "how's the weather?"
```
My Internal Process:
1. [DETECT] No development signals → Natural conversation
2. [SKIP] All template loading
3. [RESPOND] Naturally about weather
```

## Updating sessions/ Progress
```
My Internal Process:
1. [TRIGGER] Need to add timestamp to progress log
2. [BEHAVIOR] Search: "Before Adding Timestamps" in BEHAVIORS.md
3. [EXECUTE] Run: date '+%H:%M' → "14:12"
4. [WRITE] "- **14:12** - Added timestamp checking behavior"
5. [NEVER] Make up times like "14:15" without checking
```

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/examples/practical.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
