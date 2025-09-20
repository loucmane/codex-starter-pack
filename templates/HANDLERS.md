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
**Location**: [WORKFLOWS.md#handler-start-new-work](WORKFLOWS.md#handler-start-new-work)  
**Triggers**: "work on X", "let's build Y", "create feature Z"  
**Purpose**: Initialize new feature/component work  
**Related**: `continue-work`, `create-work-folder`, `save-context`

#### continue-work
**Location**: [WORKFLOWS.md#handler-continue-work](WORKFLOWS.md#handler-continue-work)  
**Triggers**: "continue X", "resume Y", "back to Z"  
**Purpose**: Resume existing work with context  
**Related**: `restore-context`, `start-new-work`

#### standard-dev-workflow
**Location**: [WORKFLOWS.md#handler-standard-dev-workflow](WORKFLOWS.md#handler-standard-dev-workflow)  
**Triggers**: "implement X", "develop Y"  
**Purpose**: Follow standard development process  
**Related**: `create-todos`, `update-tracker`

#### create-component
**Location**: [WORKFLOWS.md#handler-create-component](WORKFLOWS.md#handler-create-component)  
**Triggers**: "create component", "new component"  
**Purpose**: Create new UI/code component  
**Related**: `create-file`, `check-naming`

#### refactor-code
**Location**: [WORKFLOWS.md#handler-refactor-code](WORKFLOWS.md#handler-refactor-code)  
**Triggers**: "refactor X", "clean up Y"  
**Purpose**: Improve code structure  
**Related**: `analyze-code`, `run-tests`

### Problem Solving {#problem-solving}

#### fix-problem
**Location**: [WORKFLOWS.md#handler-fix-problem](WORKFLOWS.md#handler-fix-problem)  
**Triggers**: "fix bug", "resolve issue"  
**Purpose**: Bug fix workflow  
**Related**: `debug`, `find-references`

#### debug
**Location**: [TOOLS.md#handler-debug](TOOLS.md#handler-debug)  
**Triggers**: "debug X", "why is Y broken"  
**Purpose**: Debug code issues  
**Related**: `analyze-code`, `check-logs`

### Tool Operations {#tool-operations}

#### search-code
**Location**: [TOOLS.md#handler-search-code](TOOLS.md#handler-search-code)  
**Triggers**: "find X", "search for Y", "look for Z"  
**Purpose**: Search codebase (Serena-first)  
**Related**: `find-symbol`, `find-references`, `grep-pattern`

#### find-symbol
**Location**: [TOOLS.md#handler-find-symbol](TOOLS.md#handler-find-symbol)  
**Triggers**: "where is class X", "find function Y"  
**Purpose**: Find specific code symbols  
**Related**: `find-references`, `search-code`

#### read-file
**Location**: [TOOLS.md#handler-read-file](TOOLS.md#handler-read-file)  
**Triggers**: "show me X", "what's in Y"  
**Purpose**: Read file contents  
**Related**: `edit-file`, `analyze-code`

#### edit-file
**Location**: [TOOLS.md#handler-edit-file](TOOLS.md#handler-edit-file)  
**Triggers**: "change X to Y", "update Z"  
**Purpose**: Modify file contents  
**Related**: `read-file`, `check-style`

#### commit-changes
**Location**: [TOOLS.md#handler-commit-changes](TOOLS.md#handler-commit-changes)  
**Triggers**: "commit", "save changes"  
**Purpose**: Execute git commit  
**Related**: `check-commit-msg`, `check-status`, `create-commit-message`

#### create-commit-message
**Location**: [WORKFLOWS.md#handler-create-commit-message](WORKFLOWS.md#handler-create-commit-message)  
**Triggers**: "write commit message", "commit message for", "what's the commit message"  
**Purpose**: Generate proper commit message following conventions  
**Related**: `check-commit-msg`, `commit-changes`

### Conventions & Standards {#conventions-standards}

#### verify-claim
**Location**: [CONVENTIONS.md#handler-verify-claim](CONVENTIONS.md#handler-verify-claim)  
**Triggers**: Making assertions about code  
**Purpose**: Require evidence for claims  
**Related**: `gather-evidence`, `cite-source`

#### check-naming
**Location**: [CONVENTIONS.md#handler-check-naming](CONVENTIONS.md#handler-check-naming)  
**Triggers**: Naming files/components  
**Purpose**: Validate naming conventions  
**Related**: `suggest-name`, `create-file`

#### check-commit-msg
**Location**: [CONVENTIONS.md#handler-check-commit-msg](CONVENTIONS.md#handler-check-commit-msg)  
**Triggers**: Before git commit  
**Purpose**: Validate commit format  
**Related**: `commit-changes`, `suggest-commit-type`

#### check-conventions-first
**Location**: [CONVENTIONS.md#handler-check-conventions-first](CONVENTIONS.md#handler-check-conventions-first)  
**Triggers**: Internal before any convention-based action  
**Purpose**: Enforce pre-action convention checks  
**Related**: `enforce-pre-flight`, `check-commit-msg`

#### enforce-pre-flight
**Location**: [CONVENTIONS.md#handler-enforce-pre-flight](CONVENTIONS.md#handler-enforce-pre-flight)  
**Triggers**: "enforce conventions", "make sure I check"  
**Purpose**: System-wide enforcement of pre-checks  
**Related**: `check-conventions-first`

### Meta & Recovery {#meta-recovery}

#### show-capabilities
**Location**: [WORKFLOWS.md#handler-show-capabilities](WORKFLOWS.md#handler-show-capabilities)  
**Triggers**: "what can you do", "help", "show commands"  
**Purpose**: Display system capabilities  
**Related**: `im-lost`, `unknown-intent`

#### unknown-intent
**Location**: [CLAUDE.md → Protocol Exceptions](CLAUDE.md#protocol-exceptions)  
**Triggers**: Unclear requests  
**Purpose**: Clarify ambiguous intent  
**Related**: `ambiguous-request`, `help-needed`

#### im-lost
**Location**: [CLAUDE.md → Protocol Exceptions](CLAUDE.md#protocol-exceptions)  
**Triggers**: "I'm lost", "help"  
**Purpose**: Reorient confused users  
**Related**: `check-progress`, `show-process`

#### wrong-path
**Location**: [CLAUDE.md → Protocol Exceptions](CLAUDE.md#protocol-exceptions)  
**Triggers**: "not what I meant", "wrong"  
**Purpose**: Correct mistaken routes  
**Related**: `restart-flow`, `unknown-intent`

### System Integration {#system-integration}

#### workflow-to-tool
**Location**: [BUILDING-BETTER.md#handler-workflow-to-tool](BUILDING-BETTER.md#handler-workflow-to-tool)  
**Triggers**: Workflow needs tool  
**Purpose**: Connect workflows to tools  
**Related**: `tool-to-convention`

#### save-context
**Location**: [BUILDING-BETTER.md#handler-save-context](BUILDING-BETTER.md#handler-save-context)  
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
- **Test Process** → `create-test-checkpoint` (WORKFLOWS.md)
- **Run Tests** → `run-tests` (TOOLS.md)  
- **Test Standards** → `testing-standards` (CONVENTIONS.md)

**Rule**: Process = WORKFLOWS, Execution = TOOLS, Standards = CONVENTIONS

### Code Review {#review-disambiguation}
**"review code"** can mean:
- **Review Process** → `code-review-workflow` (WORKFLOWS.md)
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