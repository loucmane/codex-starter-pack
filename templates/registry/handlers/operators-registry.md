---
id: operators-registry
type: registry-component
name: Operator Handlers Registry
description: Complete registry of technical operation handlers
handler_count: 31
cross_references:
  - ../index.md
  - triggers-registry.md
  - orchestrators-registry.md
---

# Operator Handlers Registry

Technical operation handlers that perform specific tasks.

## Search Operations (4 handlers)

### `search-code` {#search-code}
- **Triggers**: "find X", "search for Y", "look for Z in code"
- **Keywords**: [search, find, look, locate, where, code]
- **Process**: Routes to appropriate search tool (Serena vs Grep)
- **Location**: handlers/operators/search/search-code.md

### `find-symbol` {#find-symbol}
- **Triggers**: "where is X defined", "find class Y", "locate function Z"
- **Keywords**: [symbol, class, function, method, definition, where]
- **Process**: Uses Serena find_symbol for semantic search
- **Location**: handlers/operators/search/find-symbol.md

### `find-references` {#find-references}
- **Triggers**: "what uses X", "find references to Y", "who calls Z"
- **Keywords**: [references, uses, calls, imports, depends]
- **Process**: Finds all references to a symbol
- **Location**: handlers/operators/search/find-references.md

### `grep-pattern` {#grep-pattern}
- **Triggers**: "grep for X", "search pattern Y", "find regex Z"
- **Keywords**: [grep, pattern, regex, text, search]
- **Process**: Pattern search with Serena or Grep
- **Location**: handlers/operators/search/grep-pattern.md

## File Operations (4 handlers)

### `read-file` {#read-file}
- **Triggers**: "show me X", "what's in Y", "display Z file"
- **Keywords**: [read, show, display, view, content, file]
- **Process**: Reads file with line numbers
- **Location**: handlers/operators/file/read-file.md

### `edit-file` {#edit-file}
- **Triggers**: "change X to Y", "update Z", "modify file"
- **Keywords**: [edit, change, update, modify, fix]
- **Process**: Reads first, then edits appropriately
- **Location**: handlers/operators/development/edit-file.md

### `create-file` {#create-file}
- **Triggers**: "create new file X", "make file Y", "new Z"
- **Keywords**: [create, new, make, add, file]
- **Process**: Creates file following conventions
- **Location**: handlers/operators/file/create-file.md

### `delete-file` {#delete-file}
- **Triggers**: "remove X", "delete file Y", "get rid of Z"
- **Keywords**: [delete, remove, rm, clean, rid]
- **Process**: Checks references before deletion
- **Location**: handlers/operators/file/delete-file.md

## Git Operations (5 handlers)

### `check-status` {#check-status}
- **Triggers**: "what's changed", "git status", "show changes"
- **Keywords**: [status, changes, diff, modified, staged]
- **Process**: Shows git status with clarity
- **Location**: handlers/operators/git/check-status.md

### `commit-changes` {#commit-changes}
- **Triggers**: "commit with message X", "save changes", "commit Y"
- **Keywords**: [commit, save, gac, checkin]
- **Process**: Commits with proper format
- **Location**: handlers/operators/git/commit-changes.md

### `create-branch` {#create-branch}
- **Triggers**: "new branch for X", "create branch Y", "branch off"
- **Keywords**: [branch, new, create, checkout]
- **Process**: Creates and checks out new branch
- **Location**: handlers/operators/git/create-branch.md

### `view-history` {#view-history}
- **Triggers**: "show recent commits", "git log", "history"
- **Keywords**: [history, log, commits, recent, changes]
- **Process**: Shows commit history clearly
- **Location**: handlers/operators/git/view-history.md

### `check-commit-msg` {#check-commit-msg}
- **Triggers**: "is this commit message valid", "check commit format"
- **Keywords**: [commit, message, format, valid, conventional]
- **Process**: Validates commit message format
- **Location**: handlers/operators/git/check-commit-msg.md

## Development Operations (7 handlers)

### `analyze-code` {#analyze-code}
- **Triggers**: "analyze X for issues", "check Y quality", "review Z"
- **Keywords**: [analyze, analysis, quality, issues, review]
- **Process**: Deep code analysis with categorized findings
- **Location**: handlers/operators/development/analyze-code.md

### `check-dependencies` {#check-dependencies}
- **Triggers**: "what does X depend on", "show Y dependencies", "imports"
- **Keywords**: [dependencies, depends, imports, requires, uses]
- **Process**: Maps dependency relationships
- **Location**: handlers/operators/development/check-dependencies.md

### `measure-complexity` {#measure-complexity}
- **Triggers**: "how complex is X", "complexity of Y", "analyze complexity"
- **Keywords**: [complexity, complex, metrics, cyclomatic]
- **Process**: Calculates complexity metrics
- **Location**: handlers/operators/development/measure-complexity.md

### `build-project` {#build-project}
- **Triggers**: "build the project", "compile code", "run build"
- **Keywords**: [build, compile, bundle, webpack, vite]
- **Process**: Executes build process
- **Location**: handlers/operators/development/build-project.md

### `check-naming` {#check-naming}
- **Triggers**: "is X named correctly", "check naming of Y", "validate name"
- **Keywords**: [naming, name, convention, correct, validate]
- **Process**: Validates against naming conventions
- **Location**: handlers/operators/development/check-naming.md

### `suggest-name` {#suggest-name}
- **Triggers**: "what should I call X", "suggest name for Y", "naming ideas"
- **Keywords**: [suggest, name, ideas, call, naming]
- **Process**: Generates convention-compliant names
- **Location**: handlers/operators/development/suggest-name.md

### `format-code` {#format-code}
- **Triggers**: "format X properly", "fix formatting", "clean up style"
- **Keywords**: [format, formatting, style, clean, prettier]
- **Process**: Applies proper formatting
- **Location**: handlers/operators/development/format-code.md

## Analysis Operations (3 handlers)

### `verify-claim` {#verify-claim}
- **Triggers**: "prove X is true", "verify that Y", "confirm Z"
- **Keywords**: [verify, prove, confirm, evidence, true]
- **Process**: Gathers evidence for claims
- **Location**: handlers/operators/analysis/verify-claim.md

### `gather-evidence` {#gather-evidence}
- **Triggers**: "find evidence for X", "gather proof of Y", "show support"
- **Keywords**: [evidence, proof, support, backup, facts]
- **Process**: Searches multiple sources for evidence
- **Location**: handlers/operators/analysis/gather-evidence.md

### `cite-source` {#cite-source}
- **Triggers**: "where does this come from", "what's the source", "cite reference"
- **Keywords**: [cite, source, reference, from, where]
- **Process**: Provides exact file:line references
- **Location**: handlers/operators/analysis/cite-source.md

## Workflow Operations (8 handlers)

### `create-work-folder` {#create-work-folder}
- **Triggers**: Automatic from other handlers
- **Keywords**: [folder, tracking, organize, structure]
- **Process**: Creates 7-file structure with subfolders
- **Location**: handlers/operators/workflow/create-work-folder.md

### `workflow-to-tool` {#workflow-to-tool}
- **Triggers**: Workflow step needs tool
- **Keywords**: [workflow, tool, integration, connect]
- **Process**: Routes from workflow to appropriate tool
- **Location**: handlers/operators/workflow/workflow-to-tool.md

### `tool-to-convention` {#tool-to-convention}
- **Triggers**: Tool usage needs convention check
- **Keywords**: [tool, convention, check, validate]
- **Process**: Applies conventions before tool use
- **Location**: handlers/operators/workflow/tool-to-convention.md

### `convention-to-workflow` {#convention-to-workflow}
- **Triggers**: Convention violation needs fix
- **Keywords**: [violation, fix, workflow, correct]
- **Process**: Routes to correction workflow
- **Location**: handlers/operators/workflow/convention-to-workflow.md

### `save-context` {#save-context}
- **Triggers**: "save state", "checkpoint progress", switching tasks
- **Keywords**: [save, context, state, checkpoint]
- **Process**: Preserves current work state
- **Location**: handlers/operators/workflow/save-context.md

### `restore-context` {#restore-context}
- **Triggers**: "resume work", "continue from", "pick up where"
- **Keywords**: [restore, resume, continue, context]
- **Process**: Restores previous work state
- **Location**: handlers/operators/workflow/restore-context.md

### `switch-context` {#switch-context}
- **Triggers**: "work on something else", "switch to", "pause this"
- **Keywords**: [switch, change, context, different]
- **Process**: Clean context switch between tasks
- **Location**: handlers/operators/workflow/switch-context.md

### `resolve-work-void` {#resolve-work-void}
- **Triggers**: W=VOID in ULTRATHINK format
- **Keywords**: [work, void, resolve, context]
- **Process**: Resolves missing work context
- **Location**: handlers/operators/workflow/resolve-work-void.md

## Test Operations (2 handlers)

### `run-tests` {#run-tests}
- **Triggers**: "run tests", "test the code", "execute test suite"
- **Keywords**: [test, run, execute, suite, jest, mocha]
- **Process**: Runs project test suite
- **Location**: handlers/operators/test/run-tests.md

### `check-lint` {#check-lint}
- **Triggers**: "check code style", "run linter", "lint the code"
- **Keywords**: [lint, style, eslint, format, check]
- **Process**: Runs linter and categorizes issues
- **Location**: handlers/operators/test/check-lint.md

## Discovery Methods

- Direct Read: `templates/handlers/operators/[domain]/[handler].md`
- Serena Search: `--substring_pattern "id: [handler-name]" --relative_path "templates/handlers/operators/"`