---
id: behavioral-hooks
title: Behavioral Hooks
type: engine-component
status: stable
priority: critical
dependencies:
  - templates/BEHAVIORS.md
  - templates/conventions/
  - templates/TOOLS.md
exports:
  - work-tracking-hook
  - file-operations-hook
  - development-work-hook
  - tool-selection-hook
  - evidence-claims-hook
  - task-management-hook
  - session-management-hook
  - timestamp-accuracy-hook
  - git-operations-hook
  - testing-validation-hook
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# BEHAVIORAL HOOKS (How I Actually Work)

All my behavioral enforcement lives in a dedicated template:
```
mcp__serena__search_for_pattern --substring_pattern "[trigger-type]" --relative_path "templates/BEHAVIORS.md"
```

## Key Behaviors Enforced Automatically

- **Work Tracking** - Real-time documentation updates
- **File Operations** - Convention checking before edits
- **Development Work** - Workflow loading before coding
- **Tool Selection** - Right tool verification
- **Evidence & Claims** - Proof before assertions
- **Task Management** - TodoWrite enforcement
- **Session Management** - Compaction detection
- **Timestamp Accuracy** - Check actual time before adding timestamps
- **Git Operations** - `direct-git-execution` by default; `full-gac-command` only on explicit request; `message-payload-only` for message-only; `auth-refresh-required` when SSH/GPG cache is expired
- **Testing & Validation** - Completion verification

These create "cannot proceed without" gates that ensure proper execution naturally and automatically.

## Hook Execution Protocol

Each hook creates an enforcement gate that blocks progress until satisfied:

1. **Detection**: Trigger pattern identified in request
2. **Enforcement**: Relevant behavior template loaded
3. **Validation**: Pre-conditions checked before proceeding
4. **Execution**: Only after validation passes
5. **Verification**: Post-execution checks confirm compliance

## Protocol Echo Enforcement

Before EVERY action, state:
- "Doing X (protocol: BEHAVIORS.md#specific-anchor)"
- Must reference exact behavior section anchor
- Examples: 
  - "Creating file TRACKER.md (protocol: BEHAVIORS.md#before-creating-new-files)"
  - "Editing CHANGELOG.md (protocol: BEHAVIORS.md#before-any-file-edit)"
- Self-enforcing: Must find anchor to state it, which requires reading the behavior

## Natural Enforcement

Instead of "I should check templates", these hooks create "I cannot proceed without checking" - making template usage automatic and unavoidable. Like syntax checking prevents invalid code, behavioral hooks prevent protocol violations.

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/enforcement/behavioral-hooks.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
