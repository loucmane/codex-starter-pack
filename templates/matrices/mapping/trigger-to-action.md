---
id: trigger-to-action-matrix
title: Trigger to Action Matrix
type: decision-matrix
category: mapping
status: stable
usage: Maps behavioral triggers to their corresponding actions and handlers
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Behavior → Workflow Coverage Matrix

Maps behavioral triggers to their handlers, templates, and testing status.

## Input
Behavioral trigger or system event

## Output
Handler, template location, convention, and testing status

## Matrix

| Behavior Trigger | Handler | Template | Convention | Tested | Notes |
|-----------------|---------|----------|------------|---------|--------|
| Work Tracking | create-work-folder | templates/workflows/ | work-folder format | ❌ | Need to test folder creation |
| File Operations | check-conventions | BEHAVIORS.md | file-edit rules | ❌ | Before any edit |
| Development Work | start-new-work | templates/workflows/ | workflow process | ❌ | Full workflow test |
| Tool Selection | tool-matrix | TOOLS.md | right tool rules | ❌ | Serena vs Grep |
| Evidence & Claims | gather-evidence | BEHAVIORS.md | proof required | ❌ | Before assertions |
| Task Management | create-todos | BEHAVIORS.md | TodoWrite usage | ❌ | Start of work |
| Session Management | session-start | templates/conventions/ | sessions/ format | ❌ | Session creation |
| Timestamp Accuracy | date-check | BEHAVIORS.md | actual time only | ✅ | Just implemented |
| Git Operations (gac) | gac-format | BEHAVIORS.md | no double quotes | ❌ | Commit messages |
| Testing & Validation | test-checkpoint | templates/workflows/ | user testing | ❌ | Before complete |
| Navigation | find-handler | templates/registry | keyword lookup | ✅ | 72.5% improvement |
| Context Detection | mode-detection | CLAUDE.md | dev vs chat | ❌ | Mode switching |
| Error Recovery | error-matrix | templates/matrices/ | recovery paths | ❌ | Fallback behavior |
| Memory Usage | save-context | templates/patterns/ | memory format | ❌ | Session handoff |
| Compaction | detect-size | BEHAVIORS.md | context limits | ❌ | Auto-detection |

## Coverage Summary

- **Total Behaviors**: 15
- **Tested**: 2 (13%)
- **Untested**: 13 (87%)
- **Priority**: Test core workflows first (work tracking, file ops, development)

## Trigger Categories

### System Triggers
- Session start/end
- Context size limits
- Error conditions
- Mode switches

### User Triggers
- Commands (implement, fix, test)
- Questions (how, why, where)
- Requests (commit, deploy, document)

### Automatic Triggers
- File edits
- Git operations
- Test runs
- Build processes

## Action Types

### Pre-Action Checks
- Convention verification
- Permission validation
- Dependency checking
- Context validation

### Main Actions
- Handler execution
- Tool invocation
- Workflow following
- Template loading

### Post-Action Tasks
- Result validation
- Documentation update
- Progress tracking
- Error handling

## Trigger Priority

1. **Critical**: Safety and data integrity
2. **High**: Core functionality
3. **Medium**: Convenience features
4. **Low**: Optional enhancements

## Testing Requirements

### For Each Trigger
1. Verify trigger detection
2. Confirm handler loading
3. Test action execution
4. Validate results
5. Check side effects

### Test Categories
- **Unit**: Individual trigger/action
- **Integration**: Multi-step workflows
- **System**: End-to-end scenarios
- **Regression**: Previous issues

## Implementation Status

### Implemented
- Timestamp checking
- Navigation improvements
- Basic routing

### In Progress
- Work tracking automation
- File operation gates
- Tool selection

### Planned
- Full test coverage
- Error recovery
- Memory management
- Compaction detection

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/mapping/trigger-to-action.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
