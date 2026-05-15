# System Handlers Registry

This registry provides a unified view of all handlers across the Claude Template System. Handlers remain in their domain files but are indexed here for discovery.

## 🎯 Quick Navigation {#quick-navigation}

**By Intent Type**:
- [Development Work](#development-work) - Starting, continuing, creating
- [Problem Solving](#problem-solving) - Bugs, debugging, fixes  
- [Tool Operations](#tool-operations) - Search, edit, git, analysis
- [Conventions & Standards](#conventions--standards) - Evidence, naming, style
- [Meta & Recovery](#meta--recovery) - Errors, confusion, help
- [System Integration](#system-integration) - Cross-handler flows

**Common Ambiguities**:
- [Git Operations](#git-disambiguation) - Tool vs Convention?
- [Testing](#testing-disambiguation) - Workflow vs Tool?
- [Code Review](#review-disambiguation) - Process vs Analysis?

## 📍 Handler Registry {#handler-registry}

### Development Work {#development-work}

#### start-new-work
**Location**: [templates/handlers/triggers/development/start-new-work.md](templates/handlers/triggers/development/start-new-work.md#start-new-work)  
**Triggers**: "work on X", "let's build Y", "create feature Z"  
**Purpose**: Initialize new feature/component work  
**Related**: `continue-work`, `create-work-folder`, `save-context`

#### continue-work
**Location**: [templates/handlers/triggers/workflow/continue-work.md](templates/handlers/triggers/workflow/continue-work.md#continue-work)  
**Triggers**: "continue X", "resume Y", "back to Z"  
**Purpose**: Resume existing work with context  
**Related**: `restore-context`, `start-new-work`

#### standard-dev-workflow
**Location**: [templates/handlers/orchestrators/standard-dev-workflow.md](templates/handlers/orchestrators/standard-dev-workflow.md#standard-dev-workflow)  
**Triggers**: "implement X", "develop Y"  
**Purpose**: Follow standard development process  
**Related**: `create-todos`, `update-tracker`

#### create-component
**Location**: [templates/handlers/triggers/development/create-component.md](templates/handlers/triggers/development/create-component.md#create-component)  
**Triggers**: "create component", "new component"  
**Purpose**: Create new UI/code component  
**Related**: `create-file`, `check-naming`

#### refactor-code
**Location**: [templates/handlers/triggers/development/refactor-code.md](templates/handlers/triggers/development/refactor-code.md#refactor-code)  
**Triggers**: "refactor X", "clean up Y"  
**Purpose**: Improve code structure  
**Related**: `analyze-code`, `run-tests`

### Problem Solving {#problem-solving}

#### fix-problem
**Location**: [templates/handlers/triggers/debug/fix-bug.md](templates/handlers/triggers/debug/fix-bug.md#fix-code-bug-handler)  
**Triggers**: "fix bug", "resolve issue"  
**Purpose**: Bug fix workflow  
**Related**: `debug`, `find-references`

#### debug
**Location**: [templates/handlers/triggers/debug/debug-issue.md](templates/handlers/triggers/debug/debug-issue.md)
**Triggers**: "debug X", "why is Y broken"  
**Purpose**: Debug code issues  
**Related**: `analyze-code`, `check-logs`

### Tool Operations {#tool-operations}

#### search-code
**Location**: [templates/handlers/orchestrators/tool-selection.md](templates/handlers/orchestrators/tool-selection.md#tool-selection)
**Triggers**: "find X", "search for Y", "look for Z"  
**Purpose**: Search codebase (Serena-first)  
**Related**: `find-symbol`, `find-references`, `grep-pattern`

#### find-symbol
**Location**: [templates/handlers/orchestrators/tool-selection.md](templates/handlers/orchestrators/tool-selection.md#tool-selection)
**Triggers**: "where is class X", "find function Y"  
**Purpose**: Find specific code symbols  
**Related**: `find-references`, `search-code`

#### read-file
**Location**: [TOOLS.md](TOOLS.md)
**Triggers**: "show me X", "what's in Y"  
**Purpose**: Read file contents  
**Related**: `edit-file`, `analyze-code`

#### edit-file
**Location**: [templates/handlers/operators/development/edit-file.md](templates/handlers/operators/development/edit-file.md)
**Triggers**: "change X to Y", "update Z"  
**Purpose**: Modify file contents  
**Related**: `read-file`, `check-style`

#### commit-changes
**Location**: [templates/handlers/operators/git/create-commit-message.md](templates/handlers/operators/git/create-commit-message.md#create-commit-message)
**Triggers**: "commit", "save changes"  
**Purpose**: Execute git commit  
**Related**: `check-commit-msg`, `check-status`, `create-commit-message`

#### create-commit-message
**Location**: [templates/handlers/operators/git/create-commit-message.md](templates/handlers/operators/git/create-commit-message.md#create-commit-message)  
**Triggers**: "write commit message", "commit message for", "what's the commit message"  
**Purpose**: Generate proper commit message following conventions  
**Related**: `check-commit-msg`, `commit-changes`

### Conventions & Standards {#conventions-standards}

#### verify-claim
**Location**: [templates/handlers/operators/analysis/verify-claim.md](templates/handlers/operators/analysis/verify-claim.md#verify-claim)
**Triggers**: Making assertions about code  
**Purpose**: Require evidence for claims  
**Related**: `gather-evidence`, `cite-source`

#### check-naming
**Location**: [templates/handlers/operators/development/check-naming.md](templates/handlers/operators/development/check-naming.md#check-naming)
**Triggers**: Naming files/components  
**Purpose**: Validate naming conventions  
**Related**: `suggest-name`, `create-file`

#### check-commit-msg
**Location**: [templates/handlers/operators/git/check-commit-msg.md](templates/handlers/operators/git/check-commit-msg.md#check-commit-msg)
**Triggers**: Before git commit  
**Purpose**: Validate commit format  
**Related**: `commit-changes`, `suggest-commit-type`

#### check-conventions-first
**Location**: [templates/handlers/orchestrators/check-conventions-first.md](templates/handlers/orchestrators/check-conventions-first.md#check-conventions-first)
**Triggers**: Internal before any convention-based action  
**Purpose**: Enforce pre-action convention checks  
**Related**: `enforce-pre-flight`, `check-commit-msg`

#### enforce-pre-flight
**Location**: [templates/handlers/orchestrators/enforce-pre-flight.md](templates/handlers/orchestrators/enforce-pre-flight.md#enforce-pre-flight)
**Triggers**: "enforce conventions", "make sure I check"  
**Purpose**: System-wide enforcement of pre-checks  
**Related**: `check-conventions-first`

### Meta & Recovery {#meta-recovery}

#### show-capabilities
**Location**: [templates/handlers/triggers/session/show-capabilities.md](templates/handlers/triggers/session/show-capabilities.md#show-capabilities)  
**Triggers**: "what can you do", "help", "show commands"  
**Purpose**: Display system capabilities  
**Related**: `im-lost`, `unknown-intent`

#### unknown-intent
**Location**: root `CLAUDE.md`
**Triggers**: Unclear requests  
**Purpose**: Clarify ambiguous intent  
**Related**: `ambiguous-request`, `help-needed`

#### im-lost
**Location**: root `CLAUDE.md`
**Triggers**: "I'm lost", "help"  
**Purpose**: Reorient confused users  
**Related**: `check-progress`, `show-process`

#### wrong-path
**Location**: root `CLAUDE.md`
**Triggers**: "not what I meant", "wrong"  
**Purpose**: Correct mistaken routes  
**Related**: `restart-flow`, `unknown-intent`

### System Integration {#system-integration}

#### workflow-to-tool
**Location**: [templates/handlers/orchestrators/workflow-to-tool.md](templates/handlers/orchestrators/workflow-to-tool.md#workflow-to-tool)  
**Triggers**: Workflow needs tool  
**Purpose**: Connect workflows to tools  
**Related**: `tool-to-convention`

#### save-context
**Location**: [templates/handlers/operators/session/save-context.md](templates/handlers/operators/session/save-context.md#save-context)  
**Triggers**: "save state", "checkpoint"  
**Purpose**: Preserve work context  
**Related**: `restore-context`, `switch-context`

## 🔄 Disambiguation Guide {#disambiguation-guide}

### Git Operations {#git-disambiguation}
**"commit changes"** can mean:
- **Execute Command** → `commit-changes` (TOOLS.md) - Run git commit
- **Check Format** → `check-commit-msg` (CONVENTIONS.md) - Validate message

**Rule**: Actions go to TOOLS, standards go to CONVENTIONS

### Testing {#testing-disambiguation}
**"test this"** can mean:
- **Test Process** → `create-test-checkpoint` (templates/workflows/domain/README.md)
- **Run Tests** → `run-tests` (TOOLS.md)  
- **Test Standards** → `testing-standards` (CONVENTIONS.md)

**Rule**: Process = WORKFLOWS, Execution = TOOLS, Standards = CONVENTIONS

### Code Review {#review-disambiguation}
**"review code"** can mean:
- **Review Process** → `code-review-workflow` (templates/workflows/domain/README.md)
- **Analyze Code** → `analyze-code` (TOOLS.md)
- **Review Standards** → `review-patterns` (CONVENTIONS.md)

## 🎯 Common Patterns & Examples {#common-patterns}

### Starting Work {#starting-work}
- "work on authentication" → `start-new-work`
- "let's build user profiles" → `start-new-work`
- "create new feature X" → `start-new-work`
- "implement the login flow" → `standard-dev-workflow`

### Getting Help {#getting-help}  
- "I'm lost" → `im-lost` (Protocol Exception)
- "what can you do?" → `show-capabilities`
- "help with testing" → `show-capabilities` (filtered)
- "how do I X?" → Specific handler for X

### Vague Requests → Clarification {#vague-requests}
- "make it better" → "What aspect? Code quality/Performance/UX?"
- "fix it" → "What needs fixing? Show me the error/issue"
- "test this" → "Test what? The changes/specific feature/entire app?"
- "check it" → "Check what? Code quality/tests/git status?"

### Context Resolution {#context-resolution}
- "debug this" → "What are you trying to debug? The last error/current feature?"
- "commit it" → "Commit what? All changes/specific files?"
- "search for that" → "Search for what? The last thing we discussed?"

## 🔍 Search Tips {#search-tips}

1. **By trigger phrase**: Search for quoted phrases like "work on"
2. **By handler name**: Search for exact handler like "start-new-work"
3. **By category**: Jump to sections via Quick Navigation
4. **By relationship**: Follow "Related" links

## 📊 Coverage Matrix {#coverage-matrix}

| Category | Handlers | Location | Status |
|----------|----------|----------|--------|
| Intent Handlers | 23 | templates/workflows/ | ✅ Complete |
| Tool Selection | 18 | TOOLS.md | ✅ Complete |
| Convention Handlers | 15 | templates/conventions/ | ✅ Complete |
| Protocol Exceptions | 11 | CLAUDE.md | ✅ Complete |
| Integration Handlers | 6 | templates/integration/ | ✅ Complete |
| **TOTAL** | **73** | 5 files | **100%** |

## 🔗 Adding New Handlers {#adding-new-handlers}

1. Add handler to appropriate domain file
2. Add registry entry here with same format
3. Update coverage matrix if new category
4. Add to disambiguation if ambiguous

---

Remember: This is a registry, not the source. Full handler details live in their domain files.

## Work Tracking

- **2026-05-15 15:18 CEST** - [S:20260515|W:task80-production-deployment|H:reference-remediation|E:docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/scanner-2026-05-15-reference-circular-remediation.txt] Converted stale modularization references to valid navigation/prose during Task 80 production-readiness remediation.
