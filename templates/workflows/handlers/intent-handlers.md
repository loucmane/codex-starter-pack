---
id: intent-handlers
type: workflow-component
category: handlers
title: Intent Handlers
dependencies:
  - ../patterns/task-management.md
  - ../session/lifecycle.md
related:
  - ../patterns/multi-agent-orchestration.md
version: 1.0.0
status: stable
---
> **Codex Alignment:** Replace legacy TodoWrite/TodoRead steps with the plan file + tracker checklist + Taskmaster tasks (plan update = TodoWrite, plan review = TodoRead). Always sync via `python3 scripts/codex-task plan sync` before guard checks.

# Intent Handlers

This section defines how to handle specific user intents when they're routed from CLAUDE.md's protocol-based navigation.

## Development Handlers

### Handler: start-new-work
**Triggers**: "I want to work on X", "Let's build Y", "start working on Z"
**Target Pattern**: Extract feature/component name after "on" or "build"
**Pre-conditions**: 
- Valid project context exists
- No active work folder for same feature
**Process**:
1. Extract feature name from input
2. Create work folder: `YYYYMMDD-{feature-name}-ACTIVE`
3. Initialize 7-file structure (ALL CAPS)
4. Update sessions/ with new work
5. Update plan/tracker with initial scope (plan-step-scope, tracker checklist, Taskmaster backlog entries)
6. Route to Standard Development Workflow
**Success**: Work folder created, todos initialized
**Failure**: Ask for clarification on feature name
**Examples**:
- "work on authentication" → Creates 20250712-authentication-ACTIVE
- "Let's build a meta flow creator" → Creates 20250712-meta-flow-creator-ACTIVE

### Handler: continue-work
**Triggers**: "continue with X", "back to Y", "resume Z"
**Target Pattern**: Extract work identifier after key verb
**Pre-conditions**: 
- Existing work folder must exist
- sessions/ has record of work
**Process**:
1. Search for matching work folder
2. Read current state from tracker.md
3. Review current plan/tracker status and Taskmaster tasks
4. Show current status to user
5. Resume from last checkpoint
**Success**: Previous context restored, work resumed
**Failure**: No matching work found, show available options
**Examples**:
- "continue with auth" → Finds *-authentication-ACTIVE folder
- "back to the flow creator" → Resumes meta-flow-creator work

### Handler: standard-dev-workflow
**Triggers**: "implement X", "add feature Y", "create functionality Z"
**Target Pattern**: Feature specification after action verb
**Pre-conditions**: 
- Clear feature requirements
- Work folder exists or will be created
**Process**:
1. If no work folder, route to start-new-work first
2. Break down into implementation steps
3. Create detailed todos
4. Begin with research/exploration
5. Follow TDD if applicable
6. Document as you go
**Success**: Feature implemented with tests and docs
**Failure**: Requirements unclear, needs clarification
**Examples**:
- "implement user login" → Full auth flow
- "add dark mode" → Theme system implementation

### Handler: create-component
**Triggers**: "create a new component", "build component X", "new component for Y"
**Target Pattern**: Component name and type
**Pre-conditions**: 
- Component doesn't already exist
- Valid component location identified
**Process**:
1. Check existing component patterns
2. Determine component type (UI, logic, hybrid)
3. Create component file(s)
4. Add necessary imports/exports
5. Create basic tests
6. Update component index if exists
**Success**: Component created following patterns
**Failure**: Component exists, suggest alternative
**Examples**:
- "create a Button component" → UI component with styles
- "new auth provider component" → Context/provider pattern

### Handler: refactor-code
**Triggers**: "refactor X", "clean up Y", "improve Z code"
**Target Pattern**: Code location or pattern to refactor
**Pre-conditions**: 
- Code exists and is working
- Tests exist (or will be added first)
**Process**:
1. Analyze current implementation
2. Identify refactoring opportunities
3. Ensure tests cover current behavior
4. Apply refactoring patterns
5. Verify tests still pass
6. Update documentation
**Success**: Cleaner code, same behavior, tests pass
**Failure**: No tests exist, add tests first
**Examples**:
- "refactor the auth service" → Service pattern improvements
- "clean up the API calls" → Extract to service layer

## Task Management Handlers

### Handler: create-todos
**Triggers**: "plan out X", "break down Y", "create tasks for Z"
**Target Pattern**: Work item to decompose
**Pre-conditions**: 
- Clear understanding of overall goal
- Plan/tracker + Taskmaster context available
**Process**:
1. Analyze work scope
2. Break into logical phases
3. Create hierarchical task structure
4. Set appropriate priorities
5. Log items in the plan file and Taskmaster
6. Show task breakdown to user
**Success**: Comprehensive task list created
**Failure**: Scope unclear, needs discussion
**Examples**:
- "plan out the migration" → Detailed migration steps
- "break down the feature" → Implementation tasks

### Handler: update-todos
**Triggers**: "mark X as done", "update task Y", "Z is complete"
**Target Pattern**: Task identifier or description
**Pre-conditions**: 
- Task exists in plan/tracker or Taskmaster
- Valid status transition
**Process**:
1. Find matching task(s)
2. Update status appropriately
3. Check for dependent tasks
4. Update any blockers
5. Show updated task list
**Success**: Task status updated
**Failure**: No matching task found
**Examples**:
- "mark auth tests as done" → Updates specific task
- "API integration is complete" → Finds and updates task

### Handler: check-progress
**Triggers**: "where are we?", "what's left?", "show progress"
**Target Pattern**: Optional scope filter
**Pre-conditions**: 
- Active todos exist
- Work context established  
**Process**:
1. Read current todos
2. Calculate completion percentage
3. Identify blockers
4. Show completed/remaining breakdown
5. Highlight next priorities
**Success**: Clear progress summary shown
**Failure**: No active tasks found
**Examples**:
- "where are we?" → Overall progress summary
- "what's left on auth?" → Filtered progress view

## Session Management Handlers

### Handler: show-capabilities
**Triggers**: "what can you do", "help", "show commands", "list features", "show capabilities"
**Target Pattern**: Optional focus area (e.g., "help with testing")
**Pre-conditions**: 
- None - always available
**Process**:
1. **PRIMARY**: Show categorized capabilities
   ```
   🛠️ Development: start work, create components, refactor
   🐛 Problem Solving: fix bugs, debug issues, analyze code
   🔍 Search & Navigate: find code, search patterns, explore
   📝 Documentation: explain code, write docs, add comments
   🧪 Testing: run tests, create tests, check coverage
   📊 Git Operations: commit, branch, check status
   ```
2. Highlight most common: "work on X", "fix Y", "search for Z"
3. Show example phrases for each category
4. **FALLBACK**: Link to full HANDLERS.md
**Success**: User understands available commands
**Failure**: Redirect to specific documentation
**Examples**:
- "what can you do?" → Full capability overview
- "help with testing" → Testing-specific capabilities

### Handler: start-session
**Triggers**: "let's start", "begin work", "start today's session"
**Target Pattern**: Optional continuation context
**Pre-conditions**: 
- Git repository accessible
- Previous session checked
**Process**:
1. Run date command for timestamp
2. Check git status
3. Read sessions/
4. Review recent commits
5. Ask what to work on
6. Update sessions/
**Success**: Session context established
**Failure**: Git issues, resolve first
**Examples**:
- "let's start" → Full session initialization
- "start working" → Quick session start

### Handler: update-session
**Triggers**: "update sessions/", "record progress", "checkpoint session"
**Target Pattern**: Optional specific updates
**Pre-conditions**: 
- sessions/ exists
- Work has progressed
**Process**:
1. Gather current state
2. Summarize achievements
3. Note any blockers
4. Update sessions/
5. Commit if requested
**Success**: Session record updated
**Failure**: No changes to record
**Examples**:
- "update session" → Auto-summarize progress
- "checkpoint our work" → Detailed state capture

### Handler: end-session
**Triggers**: "let's wrap up", "end for today", "finish session"
**Target Pattern**: Optional handoff notes
**Pre-conditions**: 
- Active work exists
- Changes need preservation
**Process**:
1. Final todo status check
2. Update all work tracking files
3. Create handoff notes
4. Update sessions/
5. Suggest commit message
6. Clean up any temp files
**Success**: Clean session end, ready for handoff
**Failure**: Uncommitted changes need attention
**Examples**:
- "let's wrap up" → Full end-session flow
- "done for today" → Quick wrap with essentials

### Handler: checkpoint-session
**Triggers**: Mid-session progress saves
**Target Pattern**: Automatic based on time/progress
**Pre-conditions**: 
- Significant progress made
- Time threshold passed
**Process**:
1. Auto-save current state
2. Update progress markers
3. Quick sessions/ append
4. No interruption to flow
**Success**: Progress preserved
**Failure**: Silent skip
**Examples**:
- After major milestone → Auto-checkpoint
- Every 2 hours → Time-based checkpoint

## Specialist Deployment Handlers

### Handler: deploy-ultrathink
**Triggers**: "think deeply about X", "ultrathink on Y", "need deep analysis of Z"
**Target Pattern**: Topic for analysis
**Pre-conditions**: 
- Complex problem identified
- Constraints documented
**Process**:
1. Formulate clear question
2. Gather relevant context
3. Set analysis constraints
4. Deploy ultrathink
5. Process response
6. Integrate insights
**Success**: Deep insights obtained
**Failure**: Question too vague
**Examples**:
- "think deeply about the architecture" → System design analysis
- "ultrathink on performance issues" → Optimization insights

### Handler: deploy-specialist
**Triggers**: "get expert help on X", "need specialist for Y", "deploy expert"
**Target Pattern**: Expertise area needed
**Pre-conditions**: 
- Clear task for specialist
- Constraints defined
**Process**:
1. Identify specialist type
2. Prepare task description
3. Set clear constraints
4. Deploy specialist
5. Integrate results
**Success**: Expert solution provided
**Failure**: Task unclear for specialist
**Examples**:
- "need expert on database design" → DB specialist
- "get security expert" → Security analysis

### Handler: orchestrate-complex
**Triggers**: "this needs multiple experts", "orchestrate X", "coordinate specialists for Y"
**Target Pattern**: Complex multi-domain task
**Pre-conditions**: 
- Task spans multiple domains
- Clear decomposition possible
**Process**:
1. Decompose into specialist tasks
2. Identify dependencies
3. Deploy in correct order
4. Coordinate results
5. Synthesize solutions
**Success**: Coordinated solution achieved
**Failure**: Dependencies block progress
**Examples**:
- "orchestrate full feature" → Multi-specialist flow
- "coordinate auth implementation" → Security + DB + API experts

## Testing Handlers

### Handler: create-test-checkpoint
**Triggers**: "test X", "create tests for Y", "add test coverage"
**Target Pattern**: Feature or component to test
**Pre-conditions**: 
- Code exists to test
- Test framework available
**Process**:
1. Analyze code structure
2. Identify test scenarios
3. Create test structure
4. Write test cases
5. Run and verify
6. Update coverage metrics
**Success**: Tests pass, coverage improved
**Failure**: Test framework issues
**Examples**:
- "test the auth flow" → Integration tests
- "add unit tests" → Component testing

### Handler: simulation-test
**Triggers**: "simulate X", "test workflow Y", "dry run Z"
**Target Pattern**: Workflow or process to simulate
**Pre-conditions**: 
- Workflow defined
- Simulation possible
**Process**:
1. Set up simulation env
2. Create test scenario
3. Run simulation
4. Capture results
5. Analyze outcomes
6. Report findings
**Success**: Simulation reveals insights
**Failure**: Can't simulate accurately
**Examples**:
- "simulate the migration" → Process validation
- "test the deployment flow" → Deploy simulation

### Handler: validate-changes
**Triggers**: "verify X works", "validate the changes", "confirm Y is working"
**Target Pattern**: Changes to validate
**Pre-conditions**: 
- Changes implemented
- Validation criteria clear
**Process**:
1. Identify validation points
2. Run test suites
3. Manual testing if needed
4. Check edge cases
5. Verify requirements met
6. Document results
**Success**: All validations pass
**Failure**: Issues found, document them
**Examples**:
- "verify auth works" → Full auth validation
- "validate the refactoring" → Behavior preservation

## Work Tracking Handlers

### Handler: create-work-folder
**Triggers**: Automatic from other handlers
**Target Pattern**: Work item name
**Pre-conditions**: 
- No existing folder for work
- Valid work item name
**Process**:
1. Create folder with timestamp
2. Create subfolder structure:
   - plans/ (detailed plans, roadmaps)
   - drafts/ (work-in-progress)
   - research/ (findings, references)
   - reports/ (analysis, summaries)
3. Create 6 core tracking files
4. Initialize with templates
**Success**: Complete work structure created
**Failure**: Folder already exists
**Examples**:
- From "work on auth" → 20250712-auth-ACTIVE/

### Handler: update-work-tracking
**Triggers**: After significant progress
**Target Pattern**: Automatic based on context
**Pre-conditions**: 
- Work folder exists
- Progress has been made
**Process**:
1. Update tracker.md with current state
2. Update implementation.md with code/design
3. Add to findings.md if discoveries
4. Document decisions.md rationale
5. Update memory-refs.md with context
6. Prepare handoff.md for next session
**Success**: All tracking files current
**Failure**: No folder to update
**Examples**:
- After implementing feature → Auto-update all files

## Problem Solving Handlers

### Handler: fix-bug
**Triggers**: "fix bug in X", "Y is broken", "Z isn't working"
**Target Pattern**: Bug description or location
**Pre-conditions**: 
- Bug can be reproduced
- System accessible for debugging
**Process**:
1. Reproduce the issue
2. Gather error information
3. Identify root cause
4. Implement fix
5. Test the fix
6. Prevent regression
**Success**: Bug fixed and tested
**Failure**: Can't reproduce issue
**Examples**:
- "fix login bug" → Auth debugging
- "submit button broken" → Form handler fix

### Handler: debug-issue
**Triggers**: "debug X", "investigate why Y", "find cause of Z"
**Target Pattern**: Issue to investigate
**Pre-conditions**: 
- Issue is observable
- Debug tools available
**Process**:
1. Gather symptoms
2. Form hypotheses
3. Test each hypothesis
4. Narrow down cause
5. Document findings
6. Suggest solutions
**Success**: Root cause identified
**Failure**: Insufficient information
**Examples**:
- "debug slow queries" → Performance analysis
- "why is it crashing?" → Error investigation

### Handler: optimize-code
**Triggers**: "optimize X", "make Y faster", "improve performance of Z"
**Target Pattern**: Code or feature to optimize
**Pre-conditions**: 
- Performance baseline exists
- Optimization goals clear
**Process**:
1. Measure current performance
2. Identify bottlenecks
3. Apply optimizations
4. Measure improvements
5. Verify functionality intact
6. Document changes
**Success**: Measurable improvement achieved
**Failure**: No significant improvement possible
**Examples**:
- "optimize the search" → Search algorithm improvements
- "make dashboard faster" → Rendering optimizations
- "improve API performance" → Query and caching strategies

### Handler: create-docs
**Triggers**: "document X", "write docs for Y", "create documentation", "add README"
**Target Pattern**: Code or feature to document
**Pre-conditions**: 
- Code exists and is stable
- Understand the audience (users, developers, etc.)
**Process**:
1. Determine documentation type:
   - API documentation
   - User guide
   - Developer guide
   - README file
   - Inline comments
2. Analyze what needs documenting:
   - Public APIs
   - Configuration options
   - Usage examples
   - Architecture overview
3. Follow project documentation patterns
4. Include:
   - Clear descriptions
   - Code examples
   - Common use cases
   - Troubleshooting tips
5. Place in appropriate location
**Success**: Clear, helpful documentation created
**Failure**: Documentation without examples
**Examples**:
- "document the API" → API reference docs
- "write README for auth" → Module documentation
- "create user guide" → End-user documentation

## Handler Routing Notes

These handlers are invoked through the intent routing system in CLAUDE.md. They chain together naturally to accomplish complex tasks. Each handler:

1. Has clear triggers (what invokes it)
2. Defines pre-conditions (what must be true)
3. Follows a process (step-by-step)
4. Has success/failure criteria
5. Provides concrete examples

Handlers can call other handlers, creating workflows that adapt to user needs while maintaining consistency and completeness.