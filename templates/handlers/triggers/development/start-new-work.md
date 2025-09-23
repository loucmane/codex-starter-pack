---
id: start-new-work
name: Start New Work
role: trigger
domain: development
stability: stable
triggers:
  - "I want to work on X"
  - "Let's build Y"
  - "start working on Z"
  - "work on X"
  - "begin work on X"
dependencies:
  - standard-dev-workflow
tools:
  - Write
  - TodoWrite
  - MultiEdit
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Start New Work Handler

## Purpose
Initialize a new work session by creating a properly structured work folder and setting up the development environment for a specific feature or component.

## Target Pattern
Extract feature/component name after "on" or "build" in user request.

## Pre-conditions
- Valid project context exists
- No active work folder for same feature

## Process

1. **Extract feature name from input**
   - Parse user request for feature/component name
   - Normalize name for folder creation (kebab-case)

2. **Create work folder**
   - Format: `YYYYMMDD-{feature-name}-ACTIVE`
   - Location: `/work-tracking/active/`

3. **Initialize 7-file structure** (ALL CAPS)
   - TRACKER.md - Real-time work documentation
   - sessions/ - Session management
   - HISTORY.md - Decision history
   - DEBUG.md - Problem-solving log
   - SERENA-SYNC.md - Memory integration
   - TODOS.md - Task management
   - CHANGELOG.md - Change tracking

4. **Update sessions/**
   - Add new work entry
   - Record start timestamp
   - Link to work folder

5. **Create initial todos with TodoWrite**
   - Break down feature into tasks
   - Set priorities
   - Establish checkpoints

6. **Route to Standard Development Workflow**
   - Hand off to development handler
   - Maintain context continuity

## Success Criteria
- Work folder created with complete structure
- Todos initialized and prioritized
- sessions/ updated with work entry
- Ready for development workflow

## Failure Modes
- **Unclear feature name**: Ask for clarification
- **Duplicate work folder**: Show existing work, ask to continue
- **Invalid project context**: Request project activation

## Examples

### Example 1: Simple Feature
**Input**: "work on authentication"
**Output**: Creates `20250712-authentication-ACTIVE/`
- Initializes auth-specific todos
- Sets up security considerations in TRACKER.md

### Example 2: Complex Component
**Input**: "Let's build a meta flow creator"
**Output**: Creates `20250712-meta-flow-creator-ACTIVE/`
- Breaks down into sub-components
- Creates architectural notes in HISTORY.md

### Example 3: Ambiguous Request
**Input**: "work on the thing we discussed"
**Action**: Request clarification
- "What specific feature would you like to work on?"
- Show recent work folders as options

## Integration Points

### With sessions/
- Creates new session entry
- Links work folder
- Tracks progress timestamps

### With TodoWrite
- Initializes task structure
- Sets up priority levels
- Creates milestone checkpoints

### With Standard Development Workflow
- Seamless handoff after setup
- Context preservation
- Work folder becomes active context

## Best Practices
- Always normalize feature names (kebab-case, no spaces)
- Create descriptive initial todos
- Document assumptions in TRACKER.md
- Set realistic initial milestones
- Include research/exploration tasks