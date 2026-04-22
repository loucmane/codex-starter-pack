---
id: decision-matrices
title: Decision Matrices Registry
type: registry-component
name: Decision Matrices Registry
description: Quick lookup tables for routing and decision making
status: stable
matrix_count: 5
cross_references:
  - ../index.md
  - ../navigation/keywords.md
  - ../handlers/triggers-registry.md
---

# Decision Matrices Registry

Quick lookup tables located in templates/matrices/ for rapid decision making.

## 1. Request Type → Handler Matrix

Maps user request types to appropriate handlers.

| Request Type | Example Phrases | Primary Handler | Fallback |
|--------------|----------------|-----------------|----------|
| Start Work | "work on X", "build Y" | `start-new-work` | `continue-work` |
| Fix Problem | "fix bug", "resolve issue" | `fix-bug` | `debug-issue` |
| Search Code | "find X", "where is Y" | `search-code` | `find-symbol` |
| Make Changes | "edit X", "update Y" | `edit-file` | `refactor-code` |
| Save Work | "commit", "save changes" | `commit-changes` | `check-status` |
| Create New | "create X", "new Y" | `create-component` | `create-file` |
| Test Code | "test X", "validate Y" | `create-test-checkpoint` | `run-tests` |
| Get Help | "help", "what can you do" | `show-capabilities` | `help` |
| Analyze | "explain X", "how does Y work" | `explain-code` | `analyze-code` |
| Review | "review code", "check PR" | `code-review` | `analyze-code` |

## 2. File Type → Convention Matrix

Maps file types to their specific conventions and rules.

| File Type | Naming Convention | Location Rules | Special Rules |
|-----------|------------------|----------------|---------------|
| Components | PascalCase.tsx | src/components/ | Must have tests |
| Utilities | camelCase.ts | src/utils/ | Pure functions preferred |
| Tests | *.test.ts | __tests__/ or colocated | Match source name |
| Styles | *.module.css | Colocated with component | CSS modules only |
| Configs | kebab-case.json | Project root or config/ | Validate schema |
| Documentation | UPPER-CASE.md | docs/ or root | Must have TOC |
| Work Tracking | YYYYMMDD-name-STATUS | work-tracking/ | 7-file structure; see `templates/workflows/taskmaster/work-tracking-enforcement.md` |
| Handlers | handler-name.md | handlers/[role]/[domain]/ | YAML frontmatter |

### Append-Only Files
- `TRACKER.md` - Progress Log section only
- `FINDINGS.md` - Discoveries section only  
- `sessions/` - After Current Focus section
- `HANDOFF.md` - Handoff Notes section only

### Never-Edit Files
- `package-lock.json` - Generated file
- `.git/*` - Git internals
- `node_modules/*` - Dependencies
- `build/*` - Build outputs

## 3. Problem Type → Solution Matrix

Routes different problem types to solution approaches.

| Problem Type | Indicators | Solution Approach | Handler |
|--------------|------------|-------------------|---------|
| Logic Error | Wrong output, incorrect behavior | Debug systematically | `debug-issue` |
| Syntax Error | Won't compile/run | Check syntax, linting | `check-lint` |
| Performance | Slow, timeout, memory | Profile and optimize | `optimize-code` |
| Style Issue | Inconsistent formatting | Format and lint | `format-code` |
| Type Error | TypeScript/type issues | Fix type definitions | `analyze-code` |
| Test Failure | Tests not passing | Fix code or tests | `validate-changes` |
| Build Error | Won't build/bundle | Check configs, deps | `build-project` |
| Runtime Error | Crashes when running | Debug with evidence | `debug-issue` |
| Security Issue | Vulnerabilities | Update deps, patch | `check-dependencies` |
| Architecture | Poor structure | Refactor carefully | `refactor-code` |

## 4. Context → Mode Matrix

Activates appropriate mode based on context.

| Context Indicators | Mode Activation | Key Behaviors | Handlers |
|--------------------|-----------------|---------------|----------|
| "Let's work on" | Development Mode | Load workflow, create todos | `start-new-work` |
| File paths mentioned | File Operation Mode | Check conventions first | `edit-file`, `read-file` |
| "Find/search" | Search Mode | Use right tool matrix | `search-code` |
| "Fix/broken" | Debug Mode | Gather evidence first | `fix-bug`, `debug-issue` |
| "Test/validate" | Test Mode | Comprehensive validation | `create-test-checkpoint` |
| "Commit/save" | Git Mode | Format check required | `commit-changes` |
| "Help/confused" | Assistance Mode | Provide guidance | `show-capabilities` |
| Casual chat | Natural Mode | No handlers needed | None |
| "Think about" | Analysis Mode | Deep thinking | `deploy-ultrathink` |
| Multiple requests | Orchestration Mode | Coordinate handlers | `orchestrate-complex` |

## 5. Error → Recovery Matrix

Maps errors to recovery strategies.

| Error Type | Error Messages | Recovery Strategy | Prevention |
|------------|---------------|-------------------|------------|
| File Not Found | "ENOENT", "not found" | Create or find correct path | Verify path first |
| Permission Denied | "EACCES", "permission" | Check permissions, use sudo | Check access upfront |
| Syntax Error | "SyntaxError", "unexpected" | Fix syntax, use linter | Lint before save |
| Type Error | "TypeError", "undefined" | Check types, add guards | Use TypeScript |
| Network Error | "ENETWORK", "timeout" | Retry with backoff | Add timeouts |
| Git Conflict | "conflict", "merge" | Resolve conflicts carefully | Pull before push |
| Build Failed | "build error", "webpack" | Check configs and deps | Test builds locally |
| Test Failed | "test failed", "assertion" | Fix code or update tests | TDD approach |
| Out of Memory | "ENOMEM", "heap" | Increase memory, optimize | Monitor usage |
| Module Not Found | "Cannot find module" | Install dependencies | Check package.json |

## Matrix Usage Patterns

### Quick Decision Flow
```
1. Identify situation type
2. Find relevant matrix
3. Look up row/column intersection
4. Apply recommended action
```

### Matrix Combination
Sometimes multiple matrices apply:
```
User: "Fix the component style bug"
→ Request Matrix: "fix" → fix-bug handler
→ File Matrix: "component" → src/components/ location
→ Problem Matrix: "style" → format-code approach
```

### Priority Resolution
When matrices conflict:
1. Safety matrices (permissions, git) override others
2. Problem-specific matrices override general
3. Context matrices set the mode
4. Request matrices determine handler

## Special Matrix Rules

### The "Always Check" Rule
Always consult these matrices:
- File Type matrix before any file operation
- Error Recovery matrix when errors occur
- Context Mode matrix at request start

### The "Never Skip" Rule
Never skip these checks:
- Convention matrix for file operations
- Problem matrix for debugging
- Request matrix for handler selection

### The "Fallback Chain" Rule
If primary doesn't work:
1. Try fallback handler
2. Check broader category
3. Ask for clarification
4. Document gap for improvement

## Matrix Maintenance

Matrices should be:
- **Complete** - Cover common cases
- **Current** - Updated with new patterns
- **Clear** - Unambiguous mappings
- **Concise** - Quick to scan
- **Correct** - Accurately route

## Common Matrix Lookups

### "What should I use for...?"
- Searching code? → Tool Matrix → Serena
- Editing multiple sections? → Tool Matrix → MultiEdit
- Finding problems? → Problem Matrix → debug-issue
- Starting work? → Request Matrix → start-new-work

### "Where does this go?"
- New component? → File Matrix → src/components/
- Test file? → File Matrix → __tests__/
- Documentation? → File Matrix → docs/
- Work tracking? → File Matrix → work-tracking/

### "How do I handle...?"
- Unknown request? → Request Matrix → Fallback
- File error? → Error Matrix → Recovery
- Style issue? → Problem Matrix → format-code
- Complex task? → Context Matrix → orchestrate-complex

## S:W:H:E Examples
- [S:20251027|W:task89-work-tracking|H:templates/registry/matrices/decision-matrices.md|E:templates/workflows/taskmaster/work-tracking-enforcement.md] Updated Work Tracking row with enforcement workflow reference
- [S:20251027|W:task89-work-tracking|H:templates/registry/matrices/decision-matrices.md|E:cmd`python3 scripts/codex-task work-tracking update --preset changelog --handler auto --note "Documented matrix update"`] Logged matrix maintenance in tracker/session

## Progress Log

- **2026-04-22 15:53** — [S:20260422|W:task91-standardize-template-metadata|H:templates/registry/matrices/decision-matrices.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 registry-family standardization slice
