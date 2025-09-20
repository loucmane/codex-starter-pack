---
id: triggers-registry
type: registry-component
name: Trigger Handlers Registry
description: Complete registry of user-activated trigger handlers
handler_count: 35
cross_references:
  - ../index.md
  - orchestrators-registry.md
  - operators-registry.md
---

# Trigger Handlers Registry

User-activated handlers that respond to natural language triggers.

## Development Work (5 handlers)

### `start-new-work` {#start-new-work}
- **Triggers**: "I want to work on X", "Let's build Y", "start working on Z"
- **Keywords**: [work, start, begin, new, feature, build, implement]
- **Process**: Creates work folder, initializes todos, starts workflow
- **Location**: handlers/triggers/development/start-new-work.md

### `continue-work` {#continue-work}
- **Triggers**: "continue with X", "back to Y", "resume Z"
- **Keywords**: [continue, resume, back, return, ongoing, previous]
- **Process**: Finds work folder, restores context, resumes todos
- **Location**: handlers/triggers/workflow/continue-work.md

### `create-component` {#create-component}
- **Triggers**: "create a new component", "build component X", "new component for Y"
- **Keywords**: [component, module, service, utility, class, function, hook, provider]
- **Process**: Creates new code artifacts following patterns
- **Location**: handlers/triggers/development/create-component.md

### `refactor-code` {#refactor-code}
- **Triggers**: "refactor X", "clean up Y", "improve Z code"
- **Keywords**: [refactor, cleanup, improve, restructure, optimize, modernize]
- **Process**: Ensures tests exist, refactors safely, verifies behavior
- **Location**: handlers/triggers/development/refactor-code.md

### `optimize-code` {#optimize-code}
- **Triggers**: "optimize X", "improve performance", "make faster"
- **Keywords**: [optimize, performance, speed, improve, faster]
- **Process**: Analyze performance and suggest optimizations
- **Location**: handlers/triggers/development/optimize-code.md

## Task Management (3 handlers)

### `create-todos` {#create-todos}
- **Triggers**: "plan out X", "break down Y", "create tasks for Z"
- **Keywords**: [plan, todos, tasks, breakdown, organize, steps]
- **Process**: Creates comprehensive task list with priorities
- **Location**: handlers/triggers/workflow/create-todos.md

### `update-todos` {#update-todos}
- **Triggers**: "mark X as done", "update task Y", "Z is complete"
- **Keywords**: [update, mark, done, complete, finish, progress]
- **Process**: Updates todo status, checks dependencies
- **Location**: handlers/triggers/workflow/update-todos.md

### `check-progress` {#check-progress}
- **Triggers**: "how's progress", "what's done", "show status"
- **Keywords**: [progress, status, done, completed, remaining]
- **Process**: Shows comprehensive progress across todos and tracker
- **Location**: handlers/triggers/workflow/check-progress.md

## Session Management (3 handlers)

### `start-session` {#start-session}
- **Triggers**: "let's begin", "start session", "I'm ready to work"
- **Keywords**: [session, start, begin, ready, init]
- **Process**: Initializes session context and prepares workspace
- **Location**: handlers/triggers/session/start-session.md

### `show-capabilities` {#show-capabilities}
- **Triggers**: "what can you do", "help", "show commands"
- **Keywords**: [help, capabilities, commands, what, can, do]
- **Process**: Lists available handlers and their triggers
- **Location**: handlers/triggers/session/show-capabilities.md

### `help` {#help}
- **Triggers**: "help", "I need help", "what can you do"
- **Keywords**: [help, assist, guide, explain, how]
- **Process**: Context-aware help based on current activity
- **Location**: handlers/triggers/session/help.md

## Analysis (3 handlers)

### `deploy-ultrathink` {#deploy-ultrathink}
- **Triggers**: "think deeply about X", "ultrathink on Y", "deep analysis of Z"
- **Keywords**: [ultrathink, deeply, analysis, think, complex]
- **Process**: Deploys deep thinking for complex problems
- **Location**: handlers/triggers/analysis/deploy-ultrathink.md

### `explain-code` {#explain-code}
- **Triggers**: "how does X work?", "explain this function", "what does Y do?"
- **Keywords**: [explain, how, works, what, does, understand]
- **Process**: Deep code explanation with evidence
- **Location**: handlers/triggers/analysis/explain-code.md

### `code-review` {#code-review}
- **Triggers**: "review my changes", "check this code", "review PR"
- **Keywords**: [review, check, examine, feedback, critique]
- **Process**: Systematic code review process
- **Location**: handlers/triggers/analysis/code-review.md

## Testing (3 handlers)

### `create-test-checkpoint` {#create-test-checkpoint}
- **Triggers**: "test X", "create tests for Y", "add test coverage"
- **Keywords**: [test, testing, coverage, validate, check, verify]
- **Process**: Creates test scenarios, implements tests, verifies
- **Location**: handlers/triggers/test/create-test-checkpoint.md

### `simulation-test` {#simulation-test}
- **Triggers**: "simulate X", "test workflow Y", "dry run Z"
- **Keywords**: [simulate, simulation, dry-run, mock, workflow-test]
- **Process**: Runs simulations without actual changes
- **Location**: handlers/triggers/test/simulation-test.md

### `validate-changes` {#validate-changes}
- **Triggers**: "verify X works", "validate the changes", "confirm Y is working"
- **Keywords**: [validate, verify, confirm, check, ensure, working]
- **Process**: Comprehensive validation of changes
- **Location**: handlers/triggers/test/validate-changes.md

## Work Tracking (2 handlers)

### `update-tracker` {#update-tracker}
- **Triggers**: "update progress", "log work done", "record status"
- **Keywords**: [tracker, progress, update, log, record]
- **Process**: Updates tracker.md with timestamped entries
- **Location**: handlers/triggers/workflow/update-tracker.md

### `deploy-specialist` {#deploy-specialist}
- **Triggers**: "get expert help on X", "need specialist for Y", "deploy expert"
- **Keywords**: [specialist, expert, help, deploy, assistance]
- **Process**: Deploys domain expert with constraints
- **Location**: handlers/triggers/workflow/deploy-specialist.md

## Documentation (4 handlers)

### `document-findings` {#document-findings}
- **Triggers**: "I discovered X", "found that Y", "learned Z"
- **Keywords**: [findings, discovery, learned, found, insight]
- **Process**: Documents discoveries in findings.md
- **Location**: handlers/triggers/docs/document-findings.md

### `record-decision` {#record-decision}
- **Triggers**: "decided to X", "choosing Y approach", "going with Z"
- **Keywords**: [decision, decide, choice, rationale, why]
- **Process**: Records decisions with reasoning
- **Location**: handlers/triggers/docs/record-decision.md

### `create-docs` {#create-docs}
- **Triggers**: "document X", "write docs for Y", "create documentation"
- **Keywords**: [document, docs, documentation, write, readme]
- **Process**: Generate consistent documentation
- **Location**: handlers/triggers/docs/create-docs.md

### `validate-comments` {#validate-comments}
- **Triggers**: "are these comments good", "check comment quality"
- **Keywords**: [comments, quality, review, validate]
- **Process**: Reviews comment quality
- **Location**: handlers/operators/docs/validate-comments.md

## Debugging (2 handlers)

### `fix-bug` {#fix-bug}
- **Triggers**: "fix bug X", "fix the Y bug", "resolve issue with Z"
- **Keywords**: [fix, bug, issue, problem, error, broken, resolve]
- **Process**: Routes to bug-fix-template for systematic bug resolution
- **Location**: handlers/triggers/debug/fix-bug.md

### `debug-issue` {#debug-issue}
- **Triggers**: "debug X", "debug this Y", "find the problem in Z"
- **Keywords**: [debug, trace, investigate, diagnose, troubleshoot]
- **Process**: Routes to emergency-debug template for deep investigation
- **Location**: handlers/triggers/debug/debug-issue.md

## Quick Reference

**Most Used Triggers**:
1. `start-new-work` - Begin development tasks
2. `fix-bug` - Resolve issues systematically
3. `search-code` - Find code elements
4. `commit-changes` - Save work with proper format
5. `create-test-checkpoint` - Ensure code quality

**Discovery Methods**:
- Direct Read: `templates/handlers/triggers/[domain]/[handler].md`
- Serena Search: `--substring_pattern "id: [handler-name]" --relative_path "templates/handlers/triggers/"`