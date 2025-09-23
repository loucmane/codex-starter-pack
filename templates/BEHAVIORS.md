
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Behavioral Hooks

This document contains all automatic behavioral hooks that enforce conventions and guide actions. These are the "cannot proceed without" gates that make the system work naturally.

## 🎯 Quick Navigation {#quick-navigation}

- **[ULTRATHINK Enforcement](#ultrathink-enforcement)** - MANDATORY first response
- **[Work Tracking](#work-tracking)** - Real-time documentation enforcement
- **[File Operations](#file-operations)** - Before editing any file
- **[Development Work](#development-work)** - Before implementing features
- **[Tool Selection](#tool-selection)** - Before using any tool
- **[Evidence & Claims](#evidence--claims)** - Before making assertions
- **[Task Management](#task-management)** - Before starting work
- **[Session Management](#session-management)** - Compaction detection
- **[Git Operations](#git-operations)** - Before commits and PRs
- **[Testing & Validation](#testing--validation)** - Before marking complete

## ULTRATHINK Integration {#ultrathink-integration}

This file participates in the ULTRATHINK system:

### VOID Resolution
- **S = VOID** → See [resolve-session-void](CONVENTIONS.md#resolve-session-void)
- **W = VOID** → See [resolve-work-void](WORKFLOWS.md#resolve-work-void)
- **H = VOID** → See [resolve-handler-void](registry/index.md#resolve-handler-void)

### Behavioral Enforcement
This file contains the MANDATORY enforcement hooks that ensure ULTRATHINK is used before any action.

## ULTRATHINK Enforcement {#ultrathink-enforcement}

### Before ANY Development Request {#before-any-development-request}
```
TRIGGER: Any development signal detected
ACTION: Output ULTRATHINK format
BLOCKS: Cannot proceed without valid [S:W:H:E]
PROCESS:
1. First line MUST be: "Let me ultrathink about this... [S:X|W:Y|H:Z|E:steps/"criteria"]"
2. Determine each value:
  - S: Resolve from sessions/ (use sessions/current or create)
   - W: Analyze request and active folders
   - H: Find matching handler
   - E: Count handler steps and find success criteria
3. If any value is VOID:
   - MUST resolve using appropriate handler
   - Cannot continue until resolved
4. Only after all valid → Continue to action
ERROR: Development request without ULTRATHINK
```

### Common ULTRATHINK Violations {#common-ultrathink-violations}
1. **Missing ULTRATHINK** → Stop immediately and add
2. **Old session ID** → S = VOID → resolve-session-void
3. **No work context** → W = VOID → resolve-work-void  
4. **Vague handler** → H = VOID → resolve-handler-void
5. **Skipping to action** → Return to ULTRATHINK first

### Why This Gate Exists {#why-ultrathink-gate-exists}
- Forces context awareness before action
- Prevents stale session references
- Ensures proper work organization
- Makes handler selection explicit
- Creates audit trail via [S:W:H]

## Work Tracking {#work-tracking}

### Before Starting Any Work {#before-starting-any-work}
```
TRIGGER: Beginning new development task
ACTION: Check for work tracking folder
BLOCKS: Cannot start without work tracking
PROCESS:
1. mcp__serena__search_for_pattern --substring_pattern "Create Work Tracking" --relative_path "templates/workflows/"
2. Create folder with 7-file structure (ALL CAPS) + subfolders
3. Initialize TRACKER.md with checkbox tasks from plan
CROSS-REF: See templates/workflows/ section "Create Work Tracking Folder"
```

### After Any Significant Discovery {#after-significant-discovery}
```
TRIGGER: Found bug cause, pattern, solution, or insight
ACTION: Update findings.md immediately
BLOCKS: Cannot proceed to next investigation
FORMAT:
### [Timestamp] - [Brief Title]
#### The Discovery
[What was found]
#### Why It Matters
[Impact and implications]
TIMING: Within 2 minutes of discovery
```

### After Making Decisions {#after-making-decisions}
```
TRIGGER: Chose approach, tool, pattern, or direction
ACTION: Update decisions.md with rationale
BLOCKS: Cannot implement without documenting why
FORMAT:
### [Number]. [Decision Title]
**Decision**: [What was decided]
**Rationale**: [Why this choice]
**Alternatives Considered**: [Other options]
**Evidence**: [What supports this]
TIMING: Before implementation begins
```

### After Implementation Progress {#after-implementation-progress}
```
TRIGGER: Completed todo item or reached milestone
ACTION: Update both tracker.md and implementation.md
BLOCKS: Cannot mark todo complete without updating
UPDATES:
- tracker.md: Add progress log entry with timestamp
- implementation.md: Document what was implemented
TIMING: Immediately after completion
```

### Every 30 Minutes Active Work {#every-30-minutes}
```
TRIGGER: 30 minutes elapsed during active development
ACTION: Update all relevant work tracking files
BLOCKS: Cannot continue without checkpoint
MINIMUM UPDATES:
- tracker.md: Progress log entry
- Current status of todos
- Any blockers encountered
```

### Before Context Switch {#before-context-switch}
```
TRIGGER: Switching to different task/area
ACTION: Update handoff.md with current state
BLOCKS: Cannot switch without documenting
INCLUDE:
- Exact stopping point
- Next immediate steps
- Any open questions
- File paths being worked on
```

### When Tests Fail {#when-tests-fail}
```
TRIGGER: Test failure during implementation
ACTION: Document in findings.md
BLOCKS: Cannot just fix without understanding
CAPTURE:
- Exact error message
- What was expected
- Initial hypothesis
- Fix applied
```

## File Operations {#file-operations}

### Before Any File Edit {#before-any-file-edit}
```
TRIGGER: About to use Edit/Write/MultiEdit
ACTION: mcp__serena__search_for_pattern --substring_pattern "[filename] conventions" --relative_path "templates/conventions/"
BLOCKS: Cannot edit until conventions checked
EXAMPLE: Before updating sessions/, must check session conventions
CROSS-REF: See templates/conventions/ for specific file rules
```

### Before Creating New Files {#before-creating-new-files}
```
TRIGGER: About to use Write on non-existent file
ACTION: Check if similar file exists that should be edited instead
BLOCKS: Cannot create without justification
PRINCIPLE: Always prefer editing to creating
CROSS-REF: See templates/conventions/ "File Creation Rules"
```

### Before Deleting Files {#before-deleting-files}
```
TRIGGER: Request to remove/delete files
ACTION: Verify not in .gitignore, check dependencies
BLOCKS: Cannot delete without impact analysis
EXCEPTION: Temporary files, cache files
```

## Development Work {#development-work}

### Before Implementation {#before-implementation}
```
TRIGGER: About to write new code/features  
ACTION: mcp__serena__search_for_pattern --substring_pattern "start-new-work" --relative_path "templates/registry"
THEN: Load handler from templates/workflows/
BLOCKS: Cannot code without workflow
CROSS-REF: See templates/workflows/ "Standard Development Workflow"
```

### Before Starting Any Work {#before-starting-multi-step}
```
TRIGGER: About to begin any multi-step task
ACTION: TodoWrite with comprehensive task breakdown
BLOCKS: Cannot start without task list
FORMAT:
- Break into specific, actionable items
- Include research, implementation, testing
- Mark in_progress when starting
- Complete immediately when done
CROSS-REF: See templates/workflows/ "Task Management"
```

### Before Refactoring {#before-refactoring}
```
TRIGGER: About to change existing code structure
ACTION: Ensure tests exist and pass first
BLOCKS: Cannot refactor without test safety net
PROCESS: Run tests → Refactor → Run tests again
```

## Tool Selection {#tool-selection}

### Before Tool Use {#before-tool-use}
```
TRIGGER: About to search/find anything
ACTION: mcp__serena__search_for_pattern --substring_pattern "tool-selection" --relative_path "templates/registry"
THEN: Check tool matrix for correct tool
BLOCKS: Cannot use wrong tool
CROSS-REF: See TOOLS.md "Tool Selection Matrix"
```

### Before Using Grep {#before-using-grep}
```
TRIGGER: About to search with Grep
ACTION: Consider if Serena's find_symbol would be better
BLOCKS: Use Serena for code symbols
RULE: Grep for text patterns, Serena for code understanding
CROSS-REF: See TOOLS.md "Grep vs Serena"
```

### Before Using Task Tool {#before-using-task-tool}
```
TRIGGER: Complex search or exploration needed
ACTION: Use Task tool for multi-step searches
BLOCKS: Don't do manual iteration
BENEFIT: Task tool handles complexity better
```

## Evidence & Claims {#evidence-claims}

### Before Making Claims {#before-making-claims}
```
TRIGGER: About to state facts about code
ACTION: mcp__serena__search_for_pattern --substring_pattern "evidence-check" --relative_path "templates/registry"
THEN: Gather evidence first
BLOCKS: No claims without proof
CROSS-REF: See templates/patterns/ "Evidence-Based Claims"
```

### Before Explaining How Code Works {#before-explaining-code}
```
TRIGGER: User asks "how does X work?"
ACTION: Find and read actual code first
BLOCKS: Cannot explain without seeing code
EVIDENCE: Line numbers, file paths, actual code
```

### Before Stating Dependencies {#before-stating-dependencies}
```
TRIGGER: About to say "X uses Y" or "X depends on Y"
ACTION: Verify in package.json, imports, or configs
BLOCKS: Cannot claim dependencies without proof
CHECK: Lock files, import statements, configs
```

## Task Management {#task-management}

### Before Marking Task Complete {#before-marking-task-complete}
```
TRIGGER: About to update todo status to completed
ACTION: Verify task actually done
BLOCKS: Cannot mark complete if failed/partial
CHECK:
- Implementation finished
- Tests pass (if applicable)
- Work tracking updated
- No errors or blockers
```

### Before Creating New Todos {#before-creating-new-todos}
```
TRIGGER: Adding tasks to TodoWrite
ACTION: Ensure tasks are specific and actionable
BLOCKS: No vague or compound tasks
FORMAT: Each todo should be independently completable
```

### When Todo List Gets Large {#when-todo-list-gets-large}
```
TRIGGER: More than 20 active todos
ACTION: Review and consolidate
BLOCKS: Cannot add more without cleanup
PROCESS: Complete, defer, or remove stale items
```

## Session Management {#session-management}

### Detecting Session End / Compaction Need {#detecting-session-end}
```
TRIGGER: "X% left", "let's end", "thanks", "compaction", "stop here"
ACTION: Complete session end checklist
BLOCKS: Cannot stop without providing both messages
REQUIRED OUTPUTS:

## 📦 Session End / Compaction Ready {#session-end-compaction}

**Initialization Message**:
```
mcp__serena__activate_project project="starter-pack-monorepo"
read memory session_YYYY-MM-DD_description and sessions/current.
[One line about what to continue].
```

**Git Commit Message**:
```
gac "type: one-line summary

- Major change or accomplishment
- Another significant update
- Key feature or fix

Work tracking: active-folder-names"
```

CHECKLIST COMPLETED:
✓ sessions/current updated
✓ HANDOFF.md updated with current state
✓ TRACKER.md checkboxes updated
✓ Session memory created
✓ Both messages provided above

CROSS-REF: See templates/conventions/ "Session End / Compaction Requirements"
```

### Before Creating New Session {#before-creating-new-session}
```
TRIGGER: "start new session" or beginning work
ACTION: mcp__serena__search_for_pattern --substring_pattern "session-start" --relative_path "templates/conventions/"
BLOCKS: Cannot create session without structure check
VERIFY: sessions/current symlink exists
CROSS-REF: See templates/conventions/ "Sessions directory structure"
```

### Before Ending Session {#before-ending-session}
```
TRIGGER: Work complete or switching tasks
ACTION: Update session end status in sessions/
BLOCKS: Cannot leave session undocumented
UPDATE: Progress log, session status, next steps
```

### Before Adding Timestamps {#before-adding-timestamps}
```
TRIGGER: Adding timestamp to sessions/, tracker.md, or any progress log
ACTION: 
1. Run: date '+%H:%M' (or date '+%Y-%m-%d %H:%M CEST' for full timestamp)
2. Use ACTUAL time from command output
3. NEVER make up or estimate timestamps
BLOCKS: Cannot add timestamp without checking actual time
VERIFY: Timestamp matches system time exactly
EXAMPLE: 
- ❌ "**14:15** - Tested navigation" (made up)
- ✅ Run date command first, then: "**13:56** - Tested navigation"
```

## Git Operations {#git-operations}

### When User Says "gac" {#when-user-says-gac}
```
TRIGGER: User mentions "gac" or asks for commit message
ACTION: 
1. VERIFY no double quotes inside message (would break gac)
2. CHECK conventional commit format (type: description)
3. PROVIDE raw commit message without formatting
BLOCKS: Cannot provide message in code blocks or with extra text
FORMAT:
- Just the commit message text
- No code blocks
- No "Here's your commit message:" prefix
- No formatting or markdown
- Follow conventional commit format
- Use single quotes (') inside message if needed
- NEVER use double quotes inside the message
VERIFY CHECKLIST:
□ No double quotes inside message?
□ Has type prefix (feat/fix/docs/etc)?
□ Follows format: "type: description"?
□ Any quotes inside use single quotes?
EXAMPLE: 
User: "give me gac"
AI: feat: add new feature with 'special' handling
```

### Before Any Commit {#before-any-commit}
```
TRIGGER: About to commit changes
ACTION: mcp__serena__search_for_pattern --substring_pattern "commit-changes" --relative_path "templates/REGISTRY.md"
BLOCKS: Cannot commit without convention check
VERIFY: Message format, file staging, tests pass
CROSS-REF: See TOOLS.md "Git Operations"
```

### Before Creating PR {#before-creating-pr}
```
TRIGGER: User requests pull request
ACTION: Load PR creation handler
BLOCKS: Cannot create without proper process
STEPS: Check branch, push changes, format PR body
CROSS-REF: See TOOLS.md "Creating Pull Requests"
```

### Before Git Config Changes {#before-git-config-changes}
```
TRIGGER: Any git config command
ACTION: Stop immediately
BLOCKS: NEVER modify git configuration
REASON: User's personal settings
```

## Testing & Validation {#testing-validation}

### Before Marking Task Complete {#before-marking-task-complete-validation}
```
TRIGGER: About to mark todo as completed
ACTION: Verify task actually done
BLOCKS: Cannot mark complete if failed/partial
CHECK: Tests pass, implementation complete, no errors
```

### Before Running Tests {#before-running-tests}
```
TRIGGER: Need to test implementation
ACTION: Check README or package.json for test command
BLOCKS: Cannot assume test framework
NEVER: Assume jest, mocha, etc. without checking
```

### Before Claiming "It Works" {#before-claiming-it-works}
```
TRIGGER: Implementation appears complete
ACTION: Run actual tests or validation
BLOCKS: Cannot claim success without verification
MINIMUM: Lint passes, types check, tests run
```

## Special Behaviors {#special-behaviors}

### URL Handling {#url-handling}
```
TRIGGER: Need to reference a URL
ACTION: Only use URLs from user or local files
BLOCKS: Cannot guess or generate URLs
EXCEPTION: Documentation sites if explicitly helping with programming
```

### Natural Conversation Mode {#natural-conversation-mode}
```
TRIGGER: Casual chat, no development signals
ACTION: Skip all behavioral hooks
RESPOND: Naturally without protocol
EXAMPLES: "how's the weather?", general questions
```

### Error Recovery {#error-recovery}
```
TRIGGER: Behavioral hook fails
ACTION: Check ERROR → Recovery Matrix in templates/matrices/
BLOCKS: Cannot proceed without recovery plan
FALLBACK: Ask user for guidance
CROSS-REF: See templates/matrices/ "Error → Recovery Matrix"
```

## Cross-Reference Map {#cross-reference-map}

### BEHAVIORS.md → Other Templates {#behaviors-to-other}
- Work Tracking → templates/workflows/ "Create Work Tracking Folder"
- File Operations → templates/conventions/ (specific file rules)
- Development Work → templates/workflows/ "Standard Development Workflow"
- Tool Selection → TOOLS.md "Tool Selection Matrix"
- Evidence & Claims → templates/patterns/ "Evidence-Based Claims"
- Session Management → templates/conventions/ "sessions/ Structure"
- Git Operations → TOOLS.md "Git Operations"
- Error Recovery → templates/matrices/ "Error → Recovery Matrix"

### Other Templates → BEHAVIORS.md {#other-to-behaviors}
- CLAUDE.md → "See BEHAVIORS.md for all behavioral hooks"
- templates/workflows/ → "For enforcement, see BEHAVIORS.md"
- templates/conventions/ → "Automated via BEHAVIORS.md"
- Registry → Lists all behaviors with locations

## Integration with CLAUDE.md {#integration-claude}

CLAUDE.md references these behaviors through:
```
### BEHAVIORAL HOOKS (How I Actually Work) {#behavioral-hooks-claude}
For all behavioral enforcement, see BEHAVIORS.md
These create "cannot proceed without" gates that ensure proper execution.
```

Each behavior here becomes an interrupt in my execution flow, ensuring I follow conventions naturally and automatically.

## Adding New Behaviors {#adding-new-behaviors}

When adding a new behavior:
1. Identify the trigger clearly
2. Specify the blocking action
3. Define what satisfies the gate
4. Add to appropriate section
5. Update templates/registry if needed
6. Add cross-references to related templates
7. Ensure corresponding workflow exists

Remember: Behaviors are not suggestions - they are mandatory execution gates that ensure system integrity.