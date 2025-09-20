---
id: show-capabilities
name: Show Capabilities
role: trigger
domain: session
stability: stable
triggers:
  - "what can you do"
  - "help"
  - "show commands"
  - "list features"
  - "show capabilities"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: show-capabilities {#show-capabilities}
**Triggers**: "what can you do", "help", "show commands", "list features", "show capabilities"
**Target Pattern**: Optional focus area (e.g., "help with testing")
**Pre-conditions**: 
- None - always available
**Process**:
1. **PRIMARY**: Show categorized capabilities
   ```
   🛠️ Development: start work, create components, refactor
   🐛 Problem Solving: fix bugs, debug issues, analyze code
   🔍 Search & Navigate: find code, search patterns, explore
   📝 Documentation: explain code, write docs, add comments
   🧪 Testing: run tests, create tests, check coverage
   📊 Git Operations: commit, branch, check status
   ```
2. Highlight most common: "work on X", "fix Y", "search for Z"
3. Show example phrases for each category
4. **FALLBACK**: Link to full HANDLERS.md
**Success**: User understands available commands
**Failure**: Redirect to specific documentation
**Examples**:
- "what can you do?" → Full capability overview
- "help with testing" → Testing-specific capabilities