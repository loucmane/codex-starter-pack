---
id: task-management-patterns
type: workflow-component
category: patterns
title: Task Management Patterns
dependencies:
  - ../protocols/universal-flight.md
related:
  - ../session/lifecycle.md
version: 1.0.0
status: stable
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Task Management Patterns

You have access to the TodoWrite and TodoRead tools to help manage and plan tasks. Use these tools frequently to ensure you're tracking tasks and giving visibility into progress.

## When to Use TodoWrite

Use TodoWrite proactively in these scenarios:
1. **Complex multi-step tasks** - When a task requires 3 or more distinct steps
2. **Non-trivial implementations** - Tasks requiring careful planning or multiple operations  
3. **Before starting major work** - Break down the approach into manageable steps
4. **During orchestration** - Track deployment of multiple agents or parallel work

## TodoWrite Best Practices

- Create todos BEFORE starting work, not after
- Break large tasks into specific, actionable items
- Update status in real-time (pending → in_progress → completed)
- Only have ONE task in_progress at a time
- Mark tasks complete IMMEDIATELY when done

## Example Usage

When implementing a new feature:
1. Use TodoWrite to break it down:
   - Research existing patterns
   - Design the implementation
   - Write the code
   - Add tests
   - Update documentation
2. Mark each as in_progress when starting
3. Mark as completed when done

## TodoWrite for Orchestrated Tasks

When task complexity warrants delegation:

```markdown
- [ ] 🎭 Add search functionality (orchestrated)
  - [ ] 🔍 Research: Best search libraries for our stack
  - [ ] 💻 Implementation: Core search functionality
  - [ ] ⚡ Performance: Optimize for large datasets
  - [ ] ♿ Accessibility: Screen reader support
  - [ ] 🔄 Integration: Combine all perspectives
```

Mark sub-agent tasks with emoji indicators:
- 🔍 Research tasks
- 💻 Implementation tasks
- 🔒 Security reviews
- ⚡ Performance optimization
- ♿ Accessibility compliance
- 🔄 Integration work

## Priority Levels

Always use TodoWrite with priority levels:
- 🔴 **High Priority**: Core implementation
- 🟡 **Medium Priority**: Supporting work
- 🟢 **Low Priority**: Polish and docs

Typical structure:
- Small tasks: 10-15 items
- Medium tasks: 15-25 items
- Large tasks: 25-40 items
- Complex initiatives: 40-70+ items (like template system overhaul)

## Breaking Down Complex Work

For major initiatives, create EXTENSIVE todo lists that capture EVERY step:

```markdown
Example: Template System Phase 3 (60+ todos)
- [ ] Create session entry in sessions/
- [ ] Read existing tracker to understand scope
- [ ] Read implementation plan for methodology
- [ ] Analyze CLAUDE-NEW.md section by section
- [ ] Document findings for each component
- [ ] Create work tracking folder structure
- [ ] Create tracker.md with progress tracking
- [ ] Create implementation.md with approach
- [ ] Create findings.md for discoveries
- [ ] Create decisions.md for rationale
- [ ] Create memory-refs.md for continuity
- [ ] Create handoff.md for next session
- [ ] Update main documentation with discoveries
- [ ] Add Integration Principle to workflows
- [ ] Test each integration point
- [ ] Create rollback mechanisms
- [ ] Document friction points discovered
- [ ] ... (continues for all subtasks)
```

## Benefits of Comprehensive Todo Lists

- **Nothing forgotten**: Every step is tracked
- **Clear progress**: See exactly what's done/remaining
- **Easy handoff**: Next session knows exact status
- **Prevents duplication**: Won't redo completed work
- **Mental clarity**: Offload tracking to the system

## Todo List Best Practices

1. **Granular tasks**: Break down to atomic actions
2. **Logical ordering**: Dependencies respected
3. **Clear descriptions**: Each todo self-explanatory
4. **Status tracking**: Update in real-time
5. **Review regularly**: Ensure list stays relevant

## Testing Checkpoint Pattern

```markdown
## Main Task Todo
- [ ] 🎭 Task 7: Core Layout Components (orchestrated)
  - [ ] 7.1: Create Semantic HTML Structure
    - [x] 💻 Implementation complete
    - [x] 🧪 User tested - approved
  - [ ] 7.2: Implement Header Component
    - [x] 💻 Implementation complete
    - [ ] 🧪 Awaiting user testing  ← Current checkpoint
    - [ ] 🔧 Fix any issues
    - [ ] ✅ User approval
  - [ ] 7.3: Develop Mobile Navigation
    - [ ] 💻 Implementation
    - [ ] 🧪 User testing
    - [ ] ✅ Approval
```

## Integration with Other Workflows

- TodoWrite ensures nothing is forgotten during work sessions
- Integrates with sessions/ progress tracking
- Provides clear handoff for next session
- Creates audit trail of work completed