---
id: resolve-handler-void
name: Resolve Handler VOID
role: operator
domain: workflow
stability: stable
dependencies: []
tools:
  - mcp__serena__search_for_pattern
  - Read
  - Grep
version: 1.0.0
---

#### Handler: resolve-handler-void {#resolve-handler-void}
**Triggers**: Automatic from ULTRATHINK system
**Target Pattern**: Missing handler match in ULTRATHINK S:W:H:E format
**Pre-conditions**: 
- ULTRATHINK attempted with H = VOID
- User request contains actionable intent
- templates/registry accessible for handler lookup

**Process**:
1. **Analyze User Request Intent**:
   - Extract action verbs: implement, fix, create, search, test, debug, etc.
   - Extract target nouns: component, bug, feature, function, file, etc.
   - Identify context clues: error messages, file paths, technology mentions
   - Note request complexity: single action vs multi-step workflow

2. **Search templates/registry for Handler Matches**:
   - Use mcp__serena__search_for_pattern to search Navigation Keywords section within templates/registry
   - Search pattern: extracted action verbs and nouns
   - Score matches by keyword relevance and context alignment
   - Prioritize exact phrase matches over partial matches

3. **Load Handler Definition for Validation**:
   - Read full handler definition from REGISTRY location
   - Verify handler triggers match user request intent
   - Confirm handler has required pre-conditions met
   - Check if handler is active (not marked as TO BE ADDED)

4. **Return Handler Resolution**:
   - Single clear match → Return handler name (e.g., "create-component")
   - Multiple good matches → Return primary with alternatives: "create-component (alt: standard-dev-workflow)"
   - No matches → Return "ambiguous-request" for clarification routing
   - Unclear intent → Return "show-capabilities" to guide user

**Fallback Search Strategy**:
- If Navigation Keywords fails, search all handler triggers in Intent Handlers section
- If still no match, search broader terms in handler descriptions
- For development work without clear handler, default to "start-new-work"
- For analysis/investigation requests, default to "investigate-code"

**Success**: Valid handler name returned for H field
**Failure**: No suitable handler found, returns routing pattern

**Examples**:
- "Make a new component" → Extracts: create + component → Returns: "create-component"
- "Fix this broken login" → Extracts: fix + broken → Returns: "fix-bug"
- "Find all API calls" → Extracts: find + calls → Returns: "search-code"
- "How do I..." → Extracts: help → Returns: "show-capabilities"
- "Something's wrong with..." → Extracts: wrong → Returns: "debug-issue"
- "I want to work on..." → Extracts: work → Returns: "start-new-work"

**Return Format**: 
- Success: Just the handler name (e.g., "create-component")
- With alternatives: "primary-handler (alt: alternative-handler)"
- For routing: "routing-pattern" (e.g., "ambiguous-request")