# Decision Matrices

This document contains comprehensive decision matrices for quick, accurate routing of requests and actions. Each matrix provides a scannable reference for decision-making.

## 🎯 Quick Navigation {#quick-navigation}

- **[Request Type → Handler Matrix](#request-type--handler-matrix)** - What handler for which request
- **[File Type → Convention Matrix](#file-type--convention-matrix)** - Which rules for which files
- **[Problem Type → Solution Matrix](#problem-type--solution-matrix)** - How to solve common issues
- **[Context → Mode Matrix](#context--mode-matrix)** - When to activate which mode
- **[Error → Recovery Matrix](#error--recovery-matrix)** - What to do when things fail

## ULTRATHINK Integration {#ultrathink-integration}

This file participates in the ULTRATHINK system:

### VOID Resolution
- **S = VOID** → See [resolve-session-void](CONVENTIONS.md#resolve-session-void)
- **W = VOID** → See [resolve-work-void](WORKFLOWS.md#resolve-work-void)
- **H = VOID** → See [resolve-handler-void](REGISTRY.md#resolve-handler-void)

### Matrix Usage
These matrices provide quick lookups for handler selection. When H = VOID, use the Request Type → Handler Matrix to find the appropriate handler based on the user's request pattern.

## Request Type → Handler Matrix {#request-type-handler-matrix}

| Request Pattern | Handler | Location | Example |
|-----------------|---------|----------|---------|
| "implement X" | standard-dev-workflow | WORKFLOWS.md | "implement user auth" |
| "fix X" | fix-bug | WORKFLOWS.md | "fix login bug" |
| "test X" | create-test-checkpoint | WORKFLOWS.md | "test the auth flow" |
| "find X" | search-code | TOOLS.md | "find user model" |
| "search for X" | search-code | TOOLS.md | "search for login" |
| "debug X" | debug-issue | WORKFLOWS.md | "debug auth failure" |
| "commit X" | commit-changes | TOOLS.md | "commit my changes" |
| "start session" | session-start | CONVENTIONS.md | "start new session" |
| "create work folder" | start-new-work | WORKFLOWS.md | "create work tracking" |
| "analyze X" | evidence-check | PATTERNS.md | "analyze performance" |
| "how does X work" | explain-code | PATTERNS.md | "how does auth work" |
| "refactor X" | refactor-code | WORKFLOWS.md | "refactor auth module" |
| "review X" | code-review | WORKFLOWS.md | "review my changes" |
| "document X" | create-docs | CONVENTIONS.md | "document the API" |
| "optimize X" | optimize-code | WORKFLOWS.md | "optimize queries" |
| "secure X" | security-check | TOOLS.md | "secure the endpoint" |
| "deploy X" | deployment | WORKFLOWS.md | "deploy to staging" |
| "rollback X" | rollback | WORKFLOWS.md | "rollback deployment" |
| "compare X and Y" | compare-code | PATTERNS.md | "compare v1 and v2" |

## File Type → Convention Matrix {#file-type-convention-matrix}

| File Type | Key Conventions | Handler | Special Rules |
|-----------|----------------|---------|---------------|
| sessions/ | Current Focus required, reverse chronological | session-start | Never append at bottom |
| CLAUDE.md | Execution engine, not documentation | N/A | Do not edit casually |
| *.md in work tracking | 6-file structure, timestamps | work-tracking | Update in real-time |
| memory files | Markdown format, concise | memory-write | Meaningful names |
| test files | Follow existing patterns | test-conventions | Match naming scheme |
| config files | Validate before edit | config-edit | Check dependencies |
| package.json | Version bumps carefully | package-update | Run install after |
| .gitignore | Append only | gitignore-update | Never remove entries |
| TypeScript files | Strict mode, types | ts-conventions | No any types |
| React components | Functional preferred | react-conventions | Use hooks |
| API endpoints | RESTful conventions | api-conventions | Validate inputs |
| Database schemas | Migration required | db-conventions | Never modify directly |
| Environment files | Never commit secrets | env-conventions | Use .env.example |
| Docker files | Multi-stage builds | docker-conventions | Minimize layers |
| CI/CD configs | Test before merge | cicd-conventions | Validate syntax |

## Problem Type → Solution Matrix {#problem-type-solution-matrix}

| Problem | Primary Solution | Fallback | Tools |
|---------|-----------------|----------|-------|
| Can't find symbol | find_symbol with name_path | search_for_pattern | Serena |
| Test failing | Read test, check implementation | debug-issue handler | Grep + Read |
| Build error | Check error message, find file | Fix syntax/imports | LS + Read |
| Type error | Find type definition | Add/fix types | find_symbol |
| Performance issue | Profile first | optimize-code handler | Analyze |
| Security vulnerability | security-check handler | Get expert help | Tools |
| Merge conflict | Review both sides | Manual resolution | Git |
| Deployment failure | Check logs first | Rollback if needed | Logs + Git |
| API not working | Check request/response | Debug endpoint | curl + logs |
| Database issue | Check migrations | Restore backup | psql/mysql |
| Memory leak | Profile heap | Restart service | DevTools |
| Slow queries | Analyze query plan | Add indexes | EXPLAIN |
| Race condition | Add proper locking | Refactor flow | Debug |
| Circular dependency | Map dependencies | Refactor structure | find_referencing |
| Missing handler | Search similar | Create new one | PATTERNS.md |

## Context → Mode Matrix {#context-mode-matrix}

| Context Signals | Mode | Behavior | Examples |
|----------------|------|----------|----------|
| "implement", "build", "fix" | Development Mode | Full template system | "implement search" |
| "test", "debug", "check" | Testing Mode | Evidence gathering | "test the feature" |
| "commit", "push", "PR" | Git Mode | Convention enforcement | "commit changes" |
| "search", "find", "where" | Search Mode | Tool selection matrix | "find the bug" |
| "how", "why", "explain" | Analysis Mode | Code examination | "how does it work" |
| "optimize", "improve" | Performance Mode | Profiling first | "optimize queries" |
| "secure", "vulnerability" | Security Mode | Threat analysis | "secure the API" |
| "deploy", "release" | Deployment Mode | Checklist execution | "deploy to prod" |
| "weather", "chat", general | Natural Mode | Skip all protocols | "how's the weather" |
| "document", "readme" | Documentation Mode | Markdown conventions | "document this" |
| "refactor", "clean up" | Refactoring Mode | Test preservation | "refactor auth" |
| "review", "feedback" | Review Mode | Critical analysis | "review my code" |
| "setup", "install" | Setup Mode | Environment check | "setup the project" |
| "monitor", "alert" | Monitoring Mode | Metrics focus | "monitor performance" |
| "rollback", "revert" | Recovery Mode | Safe procedures | "rollback deploy" |

## Error → Recovery Matrix {#error-recovery-matrix}

| Error Pattern | Immediate Action | Recovery Path | Prevention |
|--------------|------------------|---------------|------------|
| Handler not found | Search broader terms | Check PATTERNS.md | Update registry |
| File not found | Verify path exists | Search for file | Use absolute paths |
| Symbol not found | Try substring match | Use search_pattern | Check file first |
| Test failure | Read full error | Fix implementation | Run before commit |
| Build failure | Check recent changes | Revert if needed | Test locally |
| Type mismatch | Find type definition | Fix or cast | Use strict types |
| Import error | Check file location | Fix import path | Use aliases |
| Permission denied | Check file perms | Request access | Validate early |
| Syntax error | Find exact location | Fix syntax | Use linter |
| Network timeout | Retry with backoff | Check connection | Add timeouts |
| Memory exceeded | Reduce scope | Process in chunks | Monitor usage |
| Git conflict | Review changes | Merge carefully | Pull often |
| Database lock | Wait and retry | Kill long queries | Use transactions |
| Rate limited | Add delay | Implement backoff | Cache results |
| Version mismatch | Check requirements | Update deps | Pin versions |
| Missing dependency | Install required | Check package.json | Document deps |
| Circular reference | Map the cycle | Break dependency | Design better |
| Stack overflow | Find recursion | Add base case | Limit depth |
| Deadlock | Analyze locks | Restart service | Order locks |
| Data corruption | Restore backup | Validate data | Add checksums |

## Behavior → Workflow Coverage Matrix {#behavior-workflow-matrix}

| Behavior Trigger | Handler | Template | Convention | Tested | Notes |
|-----------------|---------|----------|------------|---------|--------|
| Work Tracking | create-work-folder | WORKFLOWS.md | work-folder format | ❌ | Need to test folder creation |
| File Operations | check-conventions | BEHAVIORS.md | file-edit rules | ❌ | Before any edit |
| Development Work | start-new-work | WORKFLOWS.md | workflow process | ❌ | Full workflow test |
| Tool Selection | tool-matrix | TOOLS.md | right tool rules | ❌ | Serena vs Grep |
| Evidence & Claims | gather-evidence | BEHAVIORS.md | proof required | ❌ | Before assertions |
| Task Management | create-todos | BEHAVIORS.md | TodoWrite usage | ❌ | Start of work |
| Session Management | session-start | CONVENTIONS.md | sessions/ format | ❌ | Session creation |
| Timestamp Accuracy | date-check | BEHAVIORS.md | actual time only | ✅ | Just implemented |
| Git Operations (gac) | gac-format | BEHAVIORS.md | no double quotes | ❌ | Commit messages |
| Testing & Validation | test-checkpoint | WORKFLOWS.md | user testing | ❌ | Before complete |
| Navigation | find-handler | REGISTRY.md | keyword lookup | ✅ | 72.5% improvement |
| Context Detection | mode-detection | CLAUDE.md | dev vs chat | ❌ | Mode switching |
| Error Recovery | error-matrix | MATRICES.md | recovery paths | ❌ | Fallback behavior |
| Memory Usage | save-context | PATTERNS.md | memory format | ❌ | Session handoff |
| Compaction | detect-size | BEHAVIORS.md | context limits | ❌ | Auto-detection |

### Coverage Summary {#coverage-summary}
- **Total Behaviors**: 15
- **Tested**: 2 (13%)
- **Untested**: 13 (87%)
- **Priority**: Test core workflows first (work tracking, file ops, development)

## Matrix Usage Patterns {#matrix-usage-patterns}

### Quick Decision Flow {#quick-decision-flow}
1. Identify request type → Find handler
2. Check file type → Apply conventions
3. Hit problem → Use solution matrix
4. Detect context → Activate mode
5. Encounter error → Follow recovery

### When to Check Matrices {#when-to-check-matrices}
- Before starting any work
- When unsure about approach
- When something fails
- When switching contexts
- When helping others

### Matrix Maintenance {#matrix-maintenance}
- Update when finding gaps
- Add new patterns discovered
- Remove obsolete entries
- Keep examples current
- Test matrix accuracy

## Integration Points {#integration-points}

### With CLAUDE.md {#with-claude-md}
- Matrices inform behavioral hooks
- Support "cannot proceed" gates
- Enable quick decisions
- Reduce lookup time

### With REGISTRY.md {#with-registry-md}
- Registry points to handlers
- Matrices show when to use
- Complementary systems
- Different purposes

### With Templates {#with-templates}
- Templates have full details
- Matrices have quick lookup
- Use together effectively
- Matrices first, then templates

## Common Matrix Queries {#common-matrix-queries}

### "What should I use for..." {#what-should-i-use}
1. Check Request Type matrix
2. Find matching pattern
3. Load indicated handler
4. Execute completely

### "What rules apply to..." {#what-rules-apply}
1. Check File Type matrix
2. Note special rules
3. Find convention handler
4. Apply all rules

### "How do I fix..." {#how-do-i-fix}
1. Check Problem Type matrix
2. Try primary solution
3. Use fallback if needed
4. Prevent future occurrence

### "What mode for..." {#what-mode-for}
1. Check Context matrix
2. Identify signals
3. Activate correct mode
4. Behave accordingly

### "What if error..." {#what-if-error}
1. Check Error matrix1
2. Take immediate action
3. Follow recovery path
4. Implement prevention

Remember: Matrices are for quick decisions. For detailed procedures, always load the full handler from the indicated template file.
