
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Claude Template System Registry - REFINED v2.0

Complete index of all handlers, templates, patterns, and conventions across the template system. 

**Version**: 2.0 (2025-07-25)
**Status**: Refined from original REGISTRY.md
**Accuracy**: 100% verified against actual template files

**CRITICAL**: This registry distinguishes between:
- **Handlers**: Have triggers and respond to user input
- **Templates**: Step-by-step guides with no triggers
- **Patterns**: Meta-routing logic for ambiguous requests
- **Behaviors**: Automatic enforcement hooks

## 📚 Essential Documentation

- **New to Claude?** → Start with [USER-GUIDE.md](USER-GUIDE.md)
- **Common workflows?** → See [WORKFLOWS.md#common-workflows](WORKFLOWS.md#common-workflows)
- **Creating handlers?** → See [BUILDING-BETTER.md#creating-handlers](BUILDING-BETTER.md#creating-handlers)
- **Having issues?** → Check [USER-GUIDE.md#troubleshooting-guide](USER-GUIDE.md#troubleshooting-guide)

## 🎯 Quick Navigation

- **[Documentation](#essential-documentation)** - User guides and tutorials 📖
- **[ULTRATHINK Resolution](#ultrathink-resolution)** - 🧠 VOID state handlers
- [Navigation Keywords](#navigation-keywords) - Keyword to handler mapping
- [Intent Handlers](#intent-handlers) - User request processing (69 handlers ✅)
- [Behavioral Templates](#behavioral-templates) - Step-by-step guides (6 templates)
- [Meta-Routing Patterns](#meta-routing-patterns) - Request routing logic (13 patterns)
- [Behavioral Hooks](#behavioral-hooks) - Automatic enforcement (9 categories)
- [Decision Matrices](#decision-matrices) - Quick lookup tables (5 matrices)
- [Special Files](#special-files) - File-specific rules
- [Common Commands](#common-commands) - Copy-paste commands

## 🧠 ULTRATHINK Resolution {#ultrathink-resolution}

**CRITICAL: These handlers resolve VOID states in the ULTRATHINK system.**

#### Handler: resolve-handler-void {#resolve-handler-void}
**Triggers**: "H = VOID", "no handler found", "handler unclear", "VOID→registry"
**Target Pattern**: Missing handler match in ULTRATHINK
**Pre-conditions**: 
- ULTRATHINK attempted
- H value is VOID
- REGISTRY accessible
**Process**:
1. Extract action keywords from user request:
   - Verbs: create, fix, search, test, etc.
   - Nouns: component, bug, function, etc.
   - Context: error messages, file names
2. Search Navigation Keywords table:
   - Match keywords to handlers
   - Score by relevance
3. If multiple matches:
   - List top 3 options
   - Ask: "Did you mean: [handler1], [handler2], or [handler3]?"
4. If no matches:
   - Search all handler triggers
   - Suggest closest matches
   - Or ask: "What specifically would you like to do?"
5. Return valid H value
**Success**: Handler identified
**Failure**: No handler matches request
**Examples**:
- "Make a component" → Finds create-component
- "Do something with code" → Too vague, asks for clarification
- "Fix the broken thing" → Suggests fix-bug or debug-issue

### ULTRATHINK Integration
This file participates in the ULTRATHINK system:
- **S = VOID** → See [resolve-session-void](handlers/orchestrators/resolve-session-void.md)
- **W = VOID** → See [resolve-work-void](handlers/operators/workflow/resolve-work-void.md)
- **H = VOID** → See [resolve-handler-void](#resolve-handler-void)

## 🔍 Navigation Keywords

Quick keyword lookup for finding handlers based on natural language.

### Action Keywords → Handlers
| Keywords | Primary Handler | Secondary Options | Location |
|----------|----------------|-------------------|----------|
| work, working, start | `start-new-work` | `continue-work` | handlers/triggers/development/start-new-work.md |
| implement, implementing, build | `standard-dev-workflow` | `start-new-work` | handlers/orchestrators/standard-dev-workflow.md |
| fix, fixing, resolve, bug | `fix-bug` | `debug-issue` | handlers/triggers/debug/fix-bug.md |
| debug, debugging, trace | `debug-issue` | `fix-bug` | handlers/triggers/debug/debug-issue.md |
| error, failing, failed | `analyze-code` | `validate-changes` | handlers/operators/development/analyze-code.md |
| search, find, looking, locate | `search-code` | `find-symbol`, `grep-pattern` | handlers/operators/search/search-code.md |
| edit, modify, update, change | `edit-file` | `refactor-code` | handlers/operators/development/edit-file.md |
| commit, save, gac | `commit-changes` | `check-commit-msg` | handlers/operators/git/commit-changes.md |
| create, new, make, add | `create-component` | `create-file` | handlers/triggers/development/create-component.md |
| test, testing, validate | `create-test-checkpoint` | `run-tests` | handlers/triggers/test/create-test-checkpoint.md |
| help, what can you do | `show-capabilities` | - | handlers/triggers/session/show-capabilities.md |
| component, module, service | `create-component` | `standard-dev-workflow` | handlers/triggers/development/create-component.md |
| refactor, clean up, improve | `refactor-code` | `review-patterns` | handlers/triggers/development/refactor-code.md |
| plan, break down, tasks | `create-todos` | `update-todos` | handlers/triggers/workflow/create-todos.md |
| progress, status, where | `check-progress` | `update-tracker` | handlers/triggers/workflow/check-progress.md |
| session, start, begin | `start-session` | `session-start` | handlers/triggers/session/start-session.md |
| ultrathink, think deeply | `deploy-ultrathink` | - | handlers/triggers/analysis/deploy-ultrathink.md |
| evidence, prove, verify | `verify-claim` | `gather-evidence` | handlers/operators/analysis/verify-claim.md |

## Intent Handlers (63 existing + 6 to add = 69 total)

Handlers that respond to user triggers and route to appropriate workflows.

### Development Work (WORKFLOWS.md) - 5 handlers

#### Handler: `start-new-work` {#start-new-work}
- **Triggers**: "I want to work on X", "Let's build Y", "start working on Z"
- **Keywords**: [work, start, begin, new, feature, build, implement]
- **Process**: Creates work folder, initializes todos, starts workflow
- **Location**: handlers/triggers/development/start-new-work.md

#### Handler: `continue-work` {#continue-work}
- **Triggers**: "continue with X", "back to Y", "resume Z"
- **Keywords**: [continue, resume, back, return, ongoing, previous]
- **Process**: Finds work folder, restores context, resumes todos
- **Location**: handlers/triggers/workflow/continue-work.md

#### Handler: `standard-dev-workflow` {#standard-dev-workflow}
- **Triggers**: "implement X", "add feature Y", "create functionality Z"
- **Keywords**: [implement, feature, functionality, develop, add, create]
- **Process**: Full development workflow with research, implementation, testing
- **Location**: handlers/orchestrators/standard-dev-workflow.md

#### Handler: `create-component` {#create-component}
- **Triggers**: "create a new component", "build component X", "new component for Y"
- **Keywords**: [component, module, service, utility, class, function, hook, provider]
- **Process**: Creates new code artifacts following patterns
- **Location**: handlers/triggers/development/create-component.md

#### Handler: `refactor-code` {#refactor-code}
- **Triggers**: "refactor X", "clean up Y", "improve Z code"
- **Keywords**: [refactor, cleanup, improve, restructure, optimize, modernize]
- **Process**: Ensures tests exist, refactors safely, verifies behavior
- **Location**: handlers/triggers/development/refactor-code.md

### Task Management (WORKFLOWS.md) - 3 handlers

#### Handler: `create-todos` {#create-todos}
- **Triggers**: "plan out X", "break down Y", "create tasks for Z"
- **Keywords**: [plan, todos, tasks, breakdown, organize, steps]
- **Process**: Creates comprehensive task list with priorities
- **Location**: handlers/triggers/workflow/create-todos.md

#### Handler: `update-todos` {#update-todos}
- **Triggers**: "mark X as done", "update task Y", "Z is complete"
- **Keywords**: [update, mark, done, complete, finish, progress]
- **Process**: Updates todo status, checks dependencies
- **Location**: handlers/triggers/workflow/update-todos.md

#### Handler: `check-progress` {#check-progress}
- **Triggers**: "where are we?", "what's left?", "show progress"
- **Keywords**: [progress, status, where, left, remaining, done]
- **Process**: Shows completion percentage, blockers, next priorities
- **Location**: handlers/triggers/workflow/check-progress.md

### Session Management (WORKFLOWS.md + CONVENTIONS.md) - 5 handlers

#### Handler: `show-capabilities` {#show-capabilities}
- **Triggers**: "what can you do", "help", "show commands"
- **Keywords**: [help, capabilities, commands, features, abilities, options]
- **Process**: Shows categorized capabilities with examples
- **Location**: handlers/triggers/session/show-capabilities.md

#### Handler: `start-session` {#start-session}
- **Triggers**: "let's start", "begin work", "start today's session"
- **Keywords**: [start, begin, session, initialize, setup]
- **Process**: Initializes session context, checks git, updates sessions/
- **Location**: handlers/triggers/session/start-session.md

#### Handler: `session-start` {#session-start-conventions}
- **Triggers**: "start new session", "begin session", "new session"
- **Keywords**: [session, start, begin, new, initialize]
- **Process**: Creates proper sessions/ structure with Current Focus
- **Location**: handlers/orchestrators/session-start.md

#### Handler: `update-session` {#update-session}
- **Triggers**: "update sessions/", "record progress", "checkpoint session"
- **Keywords**: [update, checkpoint, record, save, document]
- **Process**: Updates progress log, current state, next actions
- **Location**: handlers/triggers/session/update-session.md

#### Handler: `end-session` {#end-session}
- **Triggers**: "let's wrap up", "end for today", "finish session"
- **Keywords**: [end, wrap, finish, stop, complete, done]
- **Process**: Final updates, creates memory, provides handoff
- **Location**: handlers/triggers/session/end-session.md

#### Handler: `prepare-compaction` {#prepare-compaction}
- **Triggers**: "compaction", "% left", "context getting long", "need new chat"
- **Keywords**: [compact, compaction, memory, limit, context]
- **Process**: Creates checkpoint, preserves state, generates resume command
- **Location**: handlers/triggers/session/prepare-compaction.md

#### Handler: `checkpoint-session` {#checkpoint-session}
- **Triggers**: Mid-session automatic saves
- **Keywords**: [checkpoint, autosave, backup, snapshot]
- **Process**: Auto-saves state without interrupting flow
- **Location**: handlers/operators/session/checkpoint-session.md

### Specialist Deployment (WORKFLOWS.md) - 3 handlers

#### Handler: `deploy-ultrathink` {#deploy-ultrathink}
- **Triggers**: "think deeply about X", "ultrathink on Y", "need deep analysis"
- **Keywords**: [ultrathink, deep, analysis, think, analyze, complex]
- **Process**: Deploys deep thinking for complex problems
- **Location**: handlers/triggers/analysis/deploy-ultrathink.md

#### Handler: `deploy-specialist` {#deploy-specialist}
- **Triggers**: "get expert help on X", "need specialist for Y", "deploy expert"
- **Keywords**: [specialist, expert, help, deploy, assistance]
- **Process**: Deploys domain expert with constraints
- **Location**: handlers/triggers/workflow/deploy-specialist.md

#### Handler: `orchestrate-complex` {#orchestrate-complex}
- **Triggers**: "this needs multiple experts", "orchestrate X", "coordinate specialists"
- **Keywords**: [orchestrate, coordinate, multiple, experts, complex]
- **Process**: Coordinates multiple specialists for complex tasks
- **Location**: handlers/orchestrators/orchestrate-complex.md

### Testing (WORKFLOWS.md) - 3 handlers

#### Handler: `create-test-checkpoint` {#create-test-checkpoint}
- **Triggers**: "test X", "create tests for Y", "add test coverage"
- **Keywords**: [test, testing, coverage, validate, check, verify]
- **Process**: Creates test scenarios, implements tests, verifies
- **Location**: handlers/triggers/test/create-test-checkpoint.md

#### Handler: `simulation-test` {#simulation-test}
- **Triggers**: "simulate X", "test workflow Y", "dry run Z"
- **Keywords**: [simulate, simulation, dry-run, mock, workflow-test]
- **Process**: Runs simulations without actual changes
- **Location**: handlers/triggers/test/simulation-test.md

#### Handler: `validate-changes` {#validate-changes}
- **Triggers**: "verify X works", "validate the changes", "confirm Y is working"
- **Keywords**: [validate, verify, confirm, check, ensure, working]
- **Process**: Comprehensive validation of changes
- **Location**: handlers/triggers/test/validate-changes.md

### Work Tracking (WORKFLOWS.md) - 4 handlers

#### Handler: `create-work-folder` {#create-work-folder}
- **Triggers**: Automatic from other handlers
- **Keywords**: [folder, tracking, organize, structure]
- **Process**: Creates 7-file structure with subfolders
- **Location**: handlers/operators/workflow/create-work-folder.md

#### Handler: `update-tracker` {#update-tracker}
- **Triggers**: "update progress", "log work done", "record status"
- **Keywords**: [tracker, progress, update, log, record]
- **Process**: Updates tracker.md with timestamped entries
- **Location**: handlers/triggers/workflow/update-tracker.md

#### Handler: `document-findings` {#document-findings}
- **Triggers**: "I discovered X", "found that Y", "learned Z"
- **Keywords**: [findings, discovery, learned, found, insight]
- **Process**: Documents discoveries in findings.md
- **Location**: handlers/triggers/docs/document-findings.md

#### Handler: `record-decision` {#record-decision}
- **Triggers**: "decided to X", "choosing Y approach", "going with Z"
- **Keywords**: [decision, decide, choice, rationale, why]
- **Process**: Records decisions with reasoning
- **Location**: handlers/triggers/docs/record-decision.md

### Search Operations (TOOLS.md) - 4 handlers

#### Handler: `search-code` {#search-code}
- **Triggers**: "find X", "search for Y", "look for Z in code"
- **Keywords**: [search, find, look, locate, where, code]
- **Process**: Routes to appropriate search tool (Serena vs Grep)
- **Location**: handlers/operators/search/search-code.md

#### Handler: `find-symbol` {#find-symbol}
- **Triggers**: "where is X defined", "find class Y", "locate function Z"
- **Keywords**: [symbol, class, function, method, definition, where]
- **Process**: Uses Serena find_symbol for semantic search
- **Location**: handlers/operators/search/find-symbol.md

#### Handler: `find-references` {#find-references}
- **Triggers**: "what uses X", "find references to Y", "who calls Z"
- **Keywords**: [references, uses, calls, imports, depends]
- **Process**: Finds all references to a symbol
- **Location**: handlers/operators/search/find-references.md

#### Handler: `grep-pattern` {#grep-pattern}
- **Triggers**: "grep for X", "search pattern Y", "find regex Z"
- **Keywords**: [grep, pattern, regex, text, search]
- **Process**: Pattern search with Serena or Grep
- **Location**: handlers/operators/search/grep-pattern.md

### File Operations (TOOLS.md) - 4 handlers

#### Handler: `read-file` {#read-file}
- **Triggers**: "show me X", "what's in Y", "display Z file"
- **Keywords**: [read, show, display, view, content, file]
- **Process**: Reads file with line numbers
- **Location**: handlers/operators/file/read-file.md

#### Handler: `edit-file` {#edit-file}
- **Triggers**: "change X to Y", "update Z", "modify file"
- **Keywords**: [edit, change, update, modify, fix]
- **Process**: Reads first, then edits appropriately
- **Location**: handlers/operators/development/edit-file.md

#### Handler: `create-file` {#create-file}
- **Triggers**: "create new file X", "make file Y", "new Z"
- **Keywords**: [create, new, make, add, file]
- **Process**: Creates file following conventions
- **Location**: handlers/operators/file/create-file.md

#### Handler: `delete-file` {#delete-file}
- **Triggers**: "remove X", "delete file Y", "get rid of Z"
- **Keywords**: [delete, remove, rm, clean, rid]
- **Process**: Checks references before deletion
- **Location**: handlers/operators/file/delete-file.md

### Git Operations (TOOLS.md) - 4 handlers

#### Handler: `check-status` {#check-status}
- **Triggers**: "what's changed", "git status", "show changes"
- **Keywords**: [status, changes, diff, modified, staged]
- **Process**: Shows git status with clarity
- **Location**: handlers/operators/git/check-status.md

#### Handler: `commit-changes` {#commit-changes}
- **Triggers**: "commit with message X", "save changes", "commit Y"
- **Keywords**: [commit, save, gac, checkin]
- **Process**: Commits with proper format
- **Location**: handlers/operators/git/commit-changes.md

#### Handler: `create-branch` {#create-branch}
- **Triggers**: "new branch for X", "create branch Y", "branch off"
- **Keywords**: [branch, new, create, checkout]
- **Process**: Creates and checks out new branch
- **Location**: handlers/operators/git/create-branch.md

#### Handler: `view-history` {#view-history}
- **Triggers**: "show recent commits", "git log", "history"
- **Keywords**: [history, log, commits, recent, changes]
- **Process**: Shows commit history clearly
- **Location**: handlers/operators/git/view-history.md

### Analysis Operations (TOOLS.md) - 3 handlers

#### Handler: `analyze-code` {#analyze-code}
- **Triggers**: "analyze X for issues", "check Y quality", "review Z"
- **Keywords**: [analyze, analysis, quality, issues, review]
- **Process**: Deep code analysis with categorized findings
- **Location**: handlers/operators/development/analyze-code.md

#### Handler: `check-dependencies` {#check-dependencies}
- **Triggers**: "what does X depend on", "show Y dependencies", "imports"
- **Keywords**: [dependencies, depends, imports, requires, uses]
- **Process**: Maps dependency relationships
- **Location**: handlers/operators/development/check-dependencies.md

#### Handler: `measure-complexity` {#measure-complexity}
- **Triggers**: "how complex is X", "complexity of Y", "analyze complexity"
- **Keywords**: [complexity, complex, metrics, cyclomatic]
- **Process**: Calculates complexity metrics
- **Location**: handlers/operators/development/measure-complexity.md

### External Tools (TOOLS.md) - 3 handlers

#### Handler: `run-tests` {#run-tests}
- **Triggers**: "run tests", "test the code", "execute test suite"
- **Keywords**: [test, run, execute, suite, jest, mocha]
- **Process**: Runs project test suite
- **Location**: handlers/operators/test/run-tests.md

#### Handler: `check-lint` {#check-lint}
- **Triggers**: "check code style", "run linter", "lint the code"
- **Keywords**: [lint, style, eslint, format, check]
- **Process**: Runs linter and categorizes issues
- **Location**: handlers/operators/test/check-lint.md

#### Handler: `build-project` {#build-project}
- **Triggers**: "build the project", "compile code", "run build"
- **Keywords**: [build, compile, bundle, webpack, vite]
- **Process**: Executes build process
- **Location**: handlers/operators/development/build-project.md

### AI Integration Tools - 3 resources

#### Handler: `consult-gpt5` {#consult-gpt5}
- **Triggers**: "ask gpt5", "consult gpt5", "get second opinion", "need fresh perspective"
- **Keywords**: [gpt5, o1, cursor, second opinion, perspective, debugging]
- **Process**: Consults GPT-5 (O1 Pro) via cursor-agent for deep analysis
- **Location**: handlers/tools/external/consult-gpt5.md

#### Agent: `gpt5-analyst` {#gpt5-analyst}
- **Type**: Comprehensive analysis agent
- **Purpose**: Deep codebase analysis and architectural review
- **Tools**: Bash (cursor-agent integration)
- **Location**: agents/gpt5-analyst.md

#### Agent: `gpt5` {#gpt5}
- **Type**: Quick consultation agent
- **Purpose**: Fast second opinions and focused analysis
- **Tools**: Bash (cursor-agent integration)
- **Location**: agents/gpt5-quick.md

### Evidence & Claims (CONVENTIONS.md) - 3 handlers

#### Handler: `verify-claim` {#verify-claim}
- **Triggers**: "prove X is true", "verify that Y", "confirm Z"
- **Keywords**: [verify, prove, confirm, evidence, true]
- **Process**: Gathers evidence for claims
- **Location**: handlers/operators/analysis/verify-claim.md

#### Handler: `gather-evidence` {#gather-evidence}
- **Triggers**: "find evidence for X", "gather proof of Y", "show support"
- **Keywords**: [evidence, proof, support, backup, facts]
- **Process**: Searches multiple sources for evidence
- **Location**: handlers/operators/analysis/gather-evidence.md

#### Handler: `cite-source` {#cite-source}
- **Triggers**: "where does this come from", "what's the source", "cite reference"
- **Keywords**: [cite, source, reference, from, where]
- **Process**: Provides exact file:line references
- **Location**: handlers/operators/analysis/cite-source.md

### Naming & Style (CONVENTIONS.md) - 9 handlers

#### Handler: `check-naming` {#check-naming}
- **Triggers**: "is X named correctly", "check naming of Y", "validate name"
- **Keywords**: [naming, name, convention, correct, validate]
- **Process**: Validates against naming conventions
- **Location**: handlers/operators/development/check-naming.md

#### Handler: `suggest-name` {#suggest-name}
- **Triggers**: "what should I call X", "suggest name for Y", "naming ideas"
- **Keywords**: [suggest, name, ideas, call, naming]
- **Process**: Generates convention-compliant names
- **Location**: handlers/operators/development/suggest-name.md

#### Handler: `validate-path` {#validate-path}
- **Triggers**: "is this the right location", "check file placement", "validate path"
- **Keywords**: [path, location, placement, directory, folder]
- **Process**: Validates file locations
- **Location**: handlers/operators/file/validate-path.md

#### Handler: `check-style` {#check-style}
- **Triggers**: "does X follow conventions", "check style of Y", "review code style"
- **Keywords**: [style, conventions, format, standards]
- **Process**: Checks code style compliance
- **Location**: handlers/operators/development/check-style.md

#### Handler: `format-code` {#format-code}
- **Triggers**: "format X properly", "fix formatting", "clean up style"
- **Keywords**: [format, formatting, style, clean, prettier]
- **Process**: Applies proper formatting
- **Location**: handlers/operators/development/format-code.md

#### Handler: `review-patterns` {#review-patterns}
- **Triggers**: "is this idiomatic", "check patterns", "review approach"
- **Keywords**: [idiomatic, patterns, approach, best-practice]
- **Process**: Reviews code patterns
- **Location**: handlers/operators/development/review-patterns.md

#### Handler: `check-commit-msg` {#check-commit-msg}
- **Triggers**: "is this commit message valid", "check commit format"
- **Keywords**: [commit, message, format, valid, conventional]
- **Process**: Validates commit message format
- **Location**: handlers/operators/git/check-commit-msg.md

#### Handler: `suggest-commit-type` {#suggest-commit-type}
- **Triggers**: "what type is this change", "commit type for X"
- **Keywords**: [type, commit, feat, fix, chore]
- **Process**: Recommends commit type
- **Location**: handlers/operators/git/suggest-commit-type.md

### Documentation (CONVENTIONS.md) - 2 handlers

#### Handler: `check-docs-needed` {#check-docs-needed}
- **Triggers**: "does X need documentation", "should I document Y"
- **Keywords**: [documentation, docs, needed, required]
- **Process**: Assesses documentation needs
- **Location**: handlers/operators/docs/check-docs-needed.md

#### Handler: `validate-comments` {#validate-comments}
- **Triggers**: "are these comments good", "check comment quality"
- **Keywords**: [comments, quality, review, validate]
- **Process**: Reviews comment quality
- **Location**: handlers/operators/docs/validate-comments.md

### Pre-Check Handlers (CONVENTIONS.md) - 2 handlers

#### Handler: `check-conventions-first` {#check-conventions-first}
- **Triggers**: Internal trigger before actions
- **Keywords**: [check, conventions, first, before]
- **Process**: Mandatory convention check
- **Location**: handlers/orchestrators/check-conventions-first.md

#### Handler: `enforce-pre-flight` {#enforce-pre-flight}
- **Triggers**: "enforce conventions", "make sure I check"
- **Keywords**: [enforce, preflight, check, ensure]
- **Process**: System-wide enforcement
- **Location**: handlers/orchestrators/enforce-pre-flight.md

### Cross-System Integration (BUILDING-BETTER.md) - 6 handlers

#### Handler: `workflow-to-tool` {#workflow-to-tool}
- **Triggers**: Workflow step needs tool
- **Keywords**: [workflow, tool, integration, connect]
- **Process**: Routes from workflow to appropriate tool
- **Location**: handlers/operators/workflow/workflow-to-tool.md

#### Handler: `tool-to-convention` {#tool-to-convention}
- **Triggers**: Tool usage needs convention check
- **Keywords**: [tool, convention, check, validate]
- **Process**: Applies conventions before tool use
- **Location**: handlers/operators/workflow/tool-to-convention.md

#### Handler: `convention-to-workflow` {#convention-to-workflow}
- **Triggers**: Convention violation needs fix
- **Keywords**: [violation, fix, workflow, correct]
- **Process**: Routes to correction workflow
- **Location**: handlers/operators/workflow/convention-to-workflow.md

#### Handler: `save-context` {#save-context}
- **Triggers**: "save state", "checkpoint progress", switching tasks
- **Keywords**: [save, context, state, checkpoint]
- **Process**: Preserves current work state
- **Location**: handlers/operators/workflow/save-context.md

#### Handler: `restore-context` {#restore-context}
- **Triggers**: "resume work", "continue from", "pick up where"
- **Keywords**: [restore, resume, continue, context]
- **Process**: Restores previous work state
- **Location**: handlers/operators/workflow/restore-context.md

#### Handler: `switch-context` {#switch-context}
- **Triggers**: "work on something else", "switch to", "pause this"
- **Keywords**: [switch, change, context, different]
- **Process**: Clean context switch between tasks
- **Location**: handlers/operators/workflow/switch-context.md

### NEW HANDLERS TO ADD

#### High Priority (4 handlers) - Common User Needs

#### Handler: `fix-bug` {#fix-bug-new}
- **Triggers**: "fix bug X", "fix the Y bug", "resolve issue with Z"
- **Keywords**: [fix, bug, issue, problem, error, broken, resolve]
- **Process**: Routes to bug-fix-template for systematic bug resolution
- **Location**: handlers/triggers/debug/fix-bug.md
- **Template**: Will route to existing bug-fix-template

#### Handler: `debug-issue` {#debug-issue-new}
- **Triggers**: "debug X", "debug this Y", "find the problem in Z"
- **Keywords**: [debug, trace, investigate, diagnose, troubleshoot]
- **Process**: Routes to emergency-debug template for deep investigation
- **Location**: handlers/triggers/debug/debug-issue.md
- **Template**: Will route to existing emergency-debug template

#### Handler: `explain-code` {#explain-code}
- **Triggers**: "how does X work?", "explain this function", "what does Y do?"
- **Keywords**: [explain, how, works, what, does, understand]
- **Process**: Deep code explanation with evidence
- **Location**: handlers/triggers/analysis/explain-code.md

#### Handler: `code-review` {#code-review}
- **Triggers**: "review my changes", "check this code", "review PR"
- **Keywords**: [review, check, examine, feedback, critique]
- **Process**: Systematic code review process
- **Location**: handlers/triggers/analysis/code-review.md
- **Template**: Routes to existing code-review-template

#### Medium Priority (2 handlers) - Useful but Less Common

#### Handler: `optimize-code` {#optimize-code}
- **Triggers**: "optimize X", "improve performance", "make faster"
- **Keywords**: [optimize, performance, speed, improve, faster]
- **Process**: Analyze performance and suggest optimizations
- **Location**: handlers/triggers/development/optimize-code.md

#### Handler: `create-docs` {#create-docs}
- **Triggers**: "document X", "write docs for Y", "create documentation"
- **Keywords**: [document, docs, documentation, write, readme]
- **Process**: Generate consistent documentation
- **Location**: handlers/triggers/docs/create-docs.md

#### Low Priority (4 handlers) - Referenced in templates/matrices/ but Questionable Need

**Note**: These handlers are referenced in templates/matrices/ but may be too project-specific:
- `security-check` - Security vulnerability analysis
- `deployment` - Deploy to environments  
- `rollback` - Revert deployments
- `compare-code` - Compare two versions (could use git diff)

These are documented here for completeness but not recommended for immediate implementation.

## Behavioral Templates (6 total)

Step-by-step guides that must be manually selected (no triggers).

### Templates preserved in templates/workflows/ for reference

**IMPORTANT**: These are NOT handlers! They don't respond to triggers. Handlers route TO these templates.

1. **Feature Implementation Template** - Complete feature development steps
2. **Bug Fix Template** - Locked progression for bug fixes (used by fix-bug handler)
3. **Code Review Template** - Systematic code review process  
4. **Refactoring Template** - Safe refactoring steps
5. **Documentation Update Template** - Doc update workflow
6. **Emergency Debug Template** - Emergency debugging steps (used by debug-issue handler)

## Meta-Routing Patterns (13 total)

Patterns that route ambiguous requests to appropriate handlers.

### All located in templates/patterns/

1. `work-activity` - Routes work requests
2. `work-continuation` - Routes continuation requests
3. `file-operation` - Routes file operations
4. `file-creation` - Routes file creation
5. `tool-selection` - Routes tool choices
6. `code-creation` - Routes code creation
7. `evidence-check` - Routes evidence gathering
8. `architecture-claim` - Routes architecture verification
9. `time-capture` - Routes timestamp handling
10. `ambiguous-request` - Handles unclear requests
11. `multi-step-request` - Breaks down complex requests
12. `lost-context` - Helps reorientation
13. `system-improvement` - Routes meta-improvements


### Continuation Validation Behavior
- **Behavior**: `session/continuation-validation.md`
- **Purpose**: Guarded resumption of work (plan/tracker sync + guard evidence)
- **Usage**: Invoked automatically before continuation workflows; guard integration ensures reports/session-continuation/* contains latest log.


### Domain Workflows (Task 86)
| Workflow | Path |
|---|---|
| Session Domain Workflow | templates/workflows/domain/session.md |
| Testing Domain Workflow | templates/workflows/domain/test.md |
| Development Domain Workflow | templates/workflows/domain/development.md |
| Documentation Domain Workflow | templates/workflows/domain/docs.md |
| Analysis Domain Workflow | templates/workflows/domain/analysis.md |

## Behavioral Hooks (10 categories)

Automatic enforcement gates located in BEHAVIORS.md:

1. **Work Tracking** - Real-time documentation updates
2. **File Operations** - Convention checking before edits
3. **Development Work** - Workflow loading before coding
4. **Tool Selection** - Right tool verification
5. **Evidence & Claims** - Proof before assertions
6. **Task Management** - Taskmaster enforcement (TodoWrite replacement)
7. **Session Management** - Session end, compaction, continuation validation
8. **Timestamp Accuracy** - Check actual time before adding timestamps
9. **Continuation Validation** - Guard readiness before resuming work
10. **Git Operations** - gac format enforcement

## Decision Matrices (5 total)

Quick lookup tables located in templates/matrices/:

1. **Request Type → Handler Matrix** - Route requests to handlers
2. **File Type → Convention Matrix** - Apply file-specific rules
3. **Problem Type → Solution Matrix** - Problem-solving paths
4. **Context → Mode Matrix** - Activate appropriate modes
5. **Error → Recovery Matrix** - Error handling strategies

## Special Files

Rules for specific files (not handlers, but important conventions):

### Append-Only Files
- `TRACKER.md` - Progress Log section only
- `FINDINGS.md` - Discoveries section only
- `sessions/` - After Current Focus section

### Work Tracking Files (7-file structure)
- `IMPLEMENTATION.md` - The implementation plan
- `TRACKER.md` - Checkbox tasks tracking
- `CHANGELOG.md` - What actually changed
- `FINDINGS.md` - Discoveries and insights
- `DECISIONS.md` - Rationale for choices
- `MEMORY-REFS.md` - Related memories
- `HANDOFF.md` - Next session instructions

## Common Commands

```bash
# Timestamps - ALWAYS use for documentation
date "+%Y-%m-%d %H:%M %Z"        # Full timestamp
date +%Y%m%d                      # Folder names  
date '+%H:%M'                     # Time only for progress logs

# Git Operations
gac "commit message"              # git add . && commit
git status                        # Check before committing
git diff                          # Review changes

# Project Commands
pnpm dev                          # Start development
pnpm build                        # Build project
pnpm test                         # Run tests
pnpm typecheck                    # Check types
pnpm lint                         # Run linter
```

## Tool Selection Matrix

### Action → Tool Mapping

| I need to... | For... | MUST use... | NEVER use... |
|--------------|---------|-------------|--------------|
| Search | Code symbols | `mcp__serena__find_symbol` | grep |
| Search | References | `mcp__serena__find_referencing_symbols` | grep |
| Search | Text patterns | `mcp__serena__search_for_pattern` | - |
| Search | Simple text | `Grep` | Serena |
| Edit | ANY file | `Edit` or `MultiEdit` | Serena |
| Create | New files | `Write` | Serena |
| Read | File content | `Read` | cat/bash |
| List | Directory | `LS` | ls (bash) |
| Find | Files | `Glob` | find |
| Complex search | Multiple steps | `Task` tool | manual iteration |
| Timestamp | Documentation | `date` command | manual typing |
| Commit | Changes | `gac "message"` | git commit |

## Statistics

### Handler Breakdown by File
- **templates/workflows/**: 29 intent handlers (was 23, added 6)
- **TOOLS.md**: 18 tool selection handlers  
- **templates/conventions/**: 16 convention handlers
- **templates/integration/**: 6 integration handlers
- **AI Integration**: 1 handler + 2 agents (new)
- **templates/patterns/**: 0 (contains patterns, not handlers)
- **BEHAVIORS.md**: 0 (contains hooks, not handlers)
- **templates/matrices/**: 0 (contains matrices, not handlers)

### Totals
- **Total Existing Handlers**: 70 (was 63, added 7)
- **Total Agents**: 2 (gpt5-analyst, gpt5)
- **Handlers Added This Session**: 7
  - fix-bug ✅
  - debug-issue ✅
  - explain-code ✅
  - code-review ✅
  - optimize-code ✅
  - create-docs ✅
- **Handlers Still Missing**: 4 (low priority)
  - Low Priority: security-check, deployment, rollback, compare-code
- **Grand Total (if all added)**: 73 handlers
- **Practical Total**: 69 handlers ✅ ACHIEVED
- **Behavioral Templates**: 6 (WORKFLOWS.md)
- **Meta-Routing Patterns**: 13 (PATTERNS.md)
- **Behavioral Hooks**: 9 categories (BEHAVIORS.md)
- **Decision Matrices**: 5 (MATRICES.md)

## Registry Maintenance

When updating this registry:
1. Verify handler exists in template file
2. Check anchor name matches exactly
3. Add meaningful keywords (3+ per handler)
4. Test with Serena search
5. Update statistics if counts change

## Key Improvements in This Registry

1. **Accurate Handler Count**: 81 real handlers (not 85+)
2. **Clear Categorization**: Handlers vs Templates vs Patterns
3. **Keywords Added**: Every handler has searchable keywords
4. **Phantom Handlers Removed**: No more non-existent entries
5. **Correct Locations**: session-start is in templates/conventions/
6. **Templates Separated**: No longer confused with handlers
7. **New Handlers Identified**: Only 2 actually missing

This registry now accurately reflects the Claude Template System as it actually exists.

## Usage Guide

### How to Use This Registry

1. **Finding a Handler**:
   ```bash
   # By keyword
   mcp__serena__search_for_pattern --substring_pattern "work, working, start" --relative_path "templates/REGISTRY-REFINED.md"
   
   # By handler name  
   mcp__serena__search_for_pattern --substring_pattern "Handler: start-new-work" --relative_path "templates/workflows/"
   ```

2. **Understanding the Difference**:
   - **Handler**: "fix bug X" → triggers `fix-bug` handler → routes to bug-fix-template
   - **Template**: Step-by-step guide with no triggers, must be manually selected
   - **Pattern**: Routes ambiguous requests like "work on something"

3. **ULTRATHINK Usage**:
   - Format: `[S:sessionID|W:workContext|H:handler]`
   - Use keywords to find handlers quickly
   - Example: `[S:20250725|W:template-refinement|H:fix-bug]`

4. **Common Mistakes to Avoid**:
   - ❌ Looking for `implement-feature` (doesn't exist, use `standard-dev-workflow`)
   - ❌ Treating templates as handlers (templates have no triggers)
   - ❌ Using wrong tool (check Tool Selection Matrix)
   - ❌ Making up timestamps (always use `date` command)

## Summary: Why This Registry is Better

### Problems Fixed
1. **Phantom Handlers Removed**: No more non-existent entries like `implement-feature`, `analyze-error`
2. **Accurate Counts**: 69 handlers total (63 existing + 6 to add), not 85+
3. **Clear Distinctions**: Handlers vs Templates vs Patterns clearly separated
4. **Correct Locations**: `session-start` is in templates/conventions/, not templates/workflows/
5. **Keywords Added**: Every handler has searchable keywords for ULTRATHINK
6. **MATRICES.md Fixed**: Corrected misnamed handler references

### Key Insights
- Initially thought only 2 handlers missing, but templates/matrices/ revealed 6 more
- templates/matrices/ was aspirational - documenting ideal routing, not reality
- Templates are step-by-step guides, NOT handlers
- The system is well-designed but has gaps for common operations
- High-priority missing handlers: fix-bug, debug-issue, explain-code, code-review

### Next Steps
1. Replace original REGISTRY.md with this refined version
2. Add the 6 missing handlers (4 high priority, 2 medium)
3. Test ULTRATHINK with improved keyword discovery
4. Consider adding remaining low-priority handlers later
5. Keep templates/matrices/ and REGISTRY.md in sync