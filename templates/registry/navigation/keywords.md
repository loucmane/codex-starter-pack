---
id: navigation-keywords
type: registry-component
name: Navigation Keywords Mapping
description: Natural language keyword to handler mapping for quick discovery
cross_references:
  - ../index.md
  - ../handlers/triggers-registry.md
  - ../handlers/orchestrators-registry.md
  - ../handlers/operators-registry.md
---

# Navigation Keywords

Quick keyword lookup for finding handlers based on natural language.

## Action Keywords → Handlers

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

## Domain-Based Keywords

### Development Keywords
- **General**: code, develop, program, software, application
- **Components**: component, module, service, utility, class, function
- **Actions**: implement, build, create, develop, construct
- **Handlers**: `start-new-work`, `create-component`, `standard-dev-workflow`

### Debugging Keywords
- **Problems**: bug, issue, error, problem, broken, failing
- **Actions**: fix, debug, resolve, investigate, troubleshoot
- **Analysis**: trace, diagnose, analyze, examine
- **Handlers**: `fix-bug`, `debug-issue`, `analyze-code`

### Search Keywords
- **Actions**: find, search, locate, look, where, show
- **Targets**: symbol, reference, definition, usage, import
- **Patterns**: grep, regex, pattern, text
- **Handlers**: `search-code`, `find-symbol`, `find-references`, `grep-pattern`

### Git Keywords
- **Actions**: commit, save, push, pull, merge, branch
- **Status**: changes, modified, staged, diff, history
- **Handlers**: `commit-changes`, `check-status`, `create-branch`, `view-history`

### Testing Keywords
- **Actions**: test, validate, verify, check, ensure
- **Types**: unit, integration, coverage, suite
- **Process**: run, execute, simulate, mock
- **Handlers**: `create-test-checkpoint`, `run-tests`, `validate-changes`

### Workflow Keywords
- **Planning**: plan, organize, break down, tasks, todos
- **Progress**: status, progress, update, track, log
- **Context**: save, restore, switch, continue, resume
- **Handlers**: `create-todos`, `update-tracker`, `save-context`, `restore-context`

## Intent Recognition Patterns

### Creating Something New
**Keywords**: create, new, make, add, build, generate
**Route to**:
- Code artifact? → `create-component`
- File? → `create-file`
- Tests? → `create-test-checkpoint`
- Documentation? → `create-docs`
- Work plan? → `create-todos`

### Fixing or Debugging
**Keywords**: fix, debug, broken, error, issue, problem
**Route to**:
- Known bug? → `fix-bug`
- Need investigation? → `debug-issue`
- Code quality? → `analyze-code`

### Finding Information
**Keywords**: find, search, where, locate, show
**Route to**:
- Code symbol? → `find-symbol`
- References? → `find-references`
- Pattern/text? → `grep-pattern`
- General search? → `search-code`

### Modifying Existing Code
**Keywords**: change, edit, update, modify, refactor
**Route to**:
- File edit? → `edit-file`
- Refactoring? → `refactor-code`
- Formatting? → `format-code`

## Quick Disambiguation Guide

### "I want to..."
- **work on X** → `start-new-work`
- **fix X** → `fix-bug`
- **find X** → `search-code`
- **test X** → `create-test-checkpoint`
- **understand X** → `explain-code`
- **review X** → `code-review`
- **document X** → `create-docs`

### "Show me..."
- **the code** → `read-file`
- **what changed** → `check-status`
- **progress** → `check-progress`
- **references** → `find-references`
- **help** → `show-capabilities`

### "Create a..."
- **component** → `create-component`
- **test** → `create-test-checkpoint`
- **file** → `create-file`
- **branch** → `create-branch`
- **plan** → `create-todos`

## Usage Tips

1. **Multiple Keywords**: Combine keywords for better matching
   - "fix the login bug" → Matches both "fix" and "bug"
   - "search for the auth function" → Matches "search" and "function"

2. **Context Matters**: Same keyword can route differently based on context
   - "create" + "component" → `create-component`
   - "create" + "test" → `create-test-checkpoint`
   - "create" + "branch" → `create-branch`

3. **Fallback Strategy**: When no exact match
   - Check secondary options in table
   - Look for related domain keywords
   - Ask for clarification if ambiguous