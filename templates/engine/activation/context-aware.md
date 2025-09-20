# Context-Aware Activation

## Natural Conversation Mode (DEFAULT)
- Casual chat, questions, discussions → Respond naturally
- No routing announcements, no [CTS] tags
- System runs silently in background

## Development Mode (AUTO-TRIGGERED BY)

### Layer 1: Explicit Triggers
**Map to specific handlers**
- **Commands**: "implement", "build", "fix", "test", "debug", "work on", "create", "update", "refactor", "optimize"
- **Tools**: "search", "find", "edit", "commit", "grep", "read file"
- **Tasks**: "task", "component", "feature", "function", "module"
- **Documentation**: "document", "write README", "add comments", "API docs"

### Layer 2: Implicit Triggers
**Map to investigation/analysis**
- **Problems**: "not working", "broken", "failing", "issue", "error", "bug", "wrong", "stuck"
- **Questions**: "how does", "what's in", "where is", "why does", "can you check"
- **Analysis**: "explain this code", "what does this do", "analyze", "review"
- **Work activities**: "plan", "discuss", "design", "document", "walk through"
- **File mentions**: paths with extensions (.js, .tsx, .py, /src/, /docs/), code in backticks

### Layer 3: Behavioral Triggers
**Context-based activation**
- Following up on code discussion
- Any request that would use development tools (Read, Edit, Grep, etc.)
- Technical domain language about the project
- Error messages or stack traces in the request

### Layer 4: Protocol Echo
**Template enforcement**
- Before EVERY action: State "Doing X (protocol: BEHAVIORS.md#specific-anchor)"
- Must reference exact behavior section anchor
- Examples: 
  - "Creating file TRACKER.md (protocol: BEHAVIORS.md#before-creating-new-files)"
  - "Editing CHANGELOG.md (protocol: BEHAVIORS.md#before-any-file-edit)"
- Self-enforcing: Must find anchor to state it, which requires reading the behavior

## Mode Detection Algorithm
```
Layer 1 match → Use specific handler from REGISTRY.md
Layer 2 match → Use investigation/analysis handlers
Layer 3 match → Confirm intent: "Is this about code/development work?"
No match → Natural conversation mode
Show routing → Display [CTS] decisions when requested
```

## Uncertainty Resolution
If triggers are ambiguous, ask: "Are you asking about code/development work, or just general information?"

## Integration Points
- Feeds into Development Mode Execution when triggered
- Uses REGISTRY.md for handler mapping
- Invokes investigation patterns from templates/patterns/
- Natural mode bypasses all template protocols