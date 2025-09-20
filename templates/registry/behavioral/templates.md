---
id: behavioral-templates
type: registry-component
name: Behavioral Templates Registry
description: Step-by-step guides that must be manually selected (no triggers)
template_count: 6
cross_references:
  - ../index.md
  - ../patterns/meta-routing.md
---

# Behavioral Templates Registry

Step-by-step guides that must be manually selected (no triggers).

**IMPORTANT**: These are NOT handlers! They don't respond to triggers. Handlers route TO these templates.

## Template List

### 1. Feature Implementation Template
- **Purpose**: Complete feature development steps
- **When Used**: Routed by `standard-dev-workflow` handler
- **Process**:
  1. Research and understand requirements
  2. Design solution approach
  3. Implement with TDD
  4. Integrate and test
  5. Document and commit
- **Location**: Preserved in templates/workflows/

### 2. Bug Fix Template
- **Purpose**: Locked progression for bug fixes
- **When Used**: Routed by `fix-bug` handler
- **Process**:
  1. Reproduce the issue
  2. Gather evidence
  3. Find root cause
  4. Implement fix
  5. Verify fix works
  6. Check for regressions
- **Location**: Preserved in templates/workflows/

### 3. Code Review Template
- **Purpose**: Systematic code review process
- **When Used**: Routed by `code-review` handler
- **Process**:
  1. Understand context and goals
  2. Review architecture and design
  3. Check code quality and patterns
  4. Verify tests and coverage
  5. Provide actionable feedback
- **Location**: Preserved in templates/workflows/

### 4. Refactoring Template
- **Purpose**: Safe refactoring steps
- **When Used**: Routed by `refactor-code` handler
- **Process**:
  1. Ensure test coverage exists
  2. Identify refactoring targets
  3. Make incremental changes
  4. Verify behavior unchanged
  5. Clean up and optimize
- **Location**: Preserved in templates/workflows/

### 5. Documentation Update Template
- **Purpose**: Doc update workflow
- **When Used**: Routed by `create-docs` handler
- **Process**:
  1. Identify documentation gaps
  2. Research accurate information
  3. Write clear documentation
  4. Add examples and diagrams
  5. Review and validate
- **Location**: Preserved in templates/workflows/

### 6. Emergency Debug Template
- **Purpose**: Emergency debugging steps
- **When Used**: Routed by `debug-issue` handler
- **Process**:
  1. Capture current state
  2. Isolate the problem
  3. Form hypotheses
  4. Test systematically
  5. Document findings
  6. Implement emergency fix if needed
- **Location**: Preserved in templates/workflows/

## Key Differences: Templates vs Handlers

### Templates
- **No triggers** - Must be explicitly selected
- **Linear progression** - Follow steps in order
- **Detailed steps** - Each step fully explained
- **Manual execution** - User must invoke each step
- **Reference guides** - Can be consulted partially

### Handlers
- **Have triggers** - Respond to user input
- **Dynamic routing** - Can branch based on context
- **High-level process** - Steps summarized
- **Automatic execution** - System executes when triggered
- **Complete workflows** - Run end-to-end

## When Templates Are Used

Templates are typically invoked by handlers when:
1. A structured process must be followed exactly
2. Steps cannot be skipped or reordered
3. Each phase requires validation before proceeding
4. Documentation of each step is critical
5. The process is complex enough to need a guide

## Template Selection Matrix

| Situation | Handler Routes To | Template Used |
|-----------|------------------|---------------|
| Building new feature | `standard-dev-workflow` | Feature Implementation Template |
| Fixing a bug | `fix-bug` | Bug Fix Template |
| Reviewing code | `code-review` | Code Review Template |
| Refactoring code | `refactor-code` | Refactoring Template |
| Writing documentation | `create-docs` | Documentation Update Template |
| Emergency debugging | `debug-issue` | Emergency Debug Template |

## Usage Pattern

```
User: "Fix the login bug"
System: [Matches to fix-bug handler]
Handler: [Routes to Bug Fix Template]
Template: [Provides step-by-step guide]
User: [Follows template steps]
```

## Important Notes

1. **Templates are guides, not automation** - They provide structure but require human execution
2. **Handlers provide the automation** - They execute steps automatically
3. **Templates ensure consistency** - Same process every time
4. **Templates are teaching tools** - Help users learn proper workflows
5. **Templates can be referenced** - Don't always need to follow completely