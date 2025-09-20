---
id: trigger-phrases
type: user-guide
audience: all-users
skill-level: beginner
title: Trigger Phrases and Commands
description: Complete reference of phrases that trigger specific Claude handlers and workflows
---

# Trigger Phrases and Commands Reference

A comprehensive guide mapping what you say to what Claude does. Find the right phrase for any task!

## Quick Reference by Intent

### 🚀 Starting Something New

**Say This** → **Triggers Handler**
- "I want to work on X" → `start-new-work`
- "Let's build Y" → `start-new-work`
- "Start implementing Z" → `start-new-work`
- "Create a new feature" → `start-new-work`
- "Beginning work on..." → `start-new-work`

**Examples:**
```
"I want to work on user authentication"
"Let's build a shopping cart"
"Start implementing the payment system"
```

### 🔧 Fixing Problems

**Say This** → **Triggers Handler**
- "Fix the X bug" → `fix-bug`
- "Y is broken" → `fix-bug`
- "Z isn't working" → `fix-bug`
- "Resolve issue with..." → `fix-bug`
- "Debug why..." → `debug-issue`

**Examples:**
```
"Fix the login bug"
"The navigation menu is broken"
"Debug why users can't submit the form"
```

### 🔍 Finding Code

**Say This** → **Triggers Handler**
- "Where is X?" → `find-symbol`
- "Find Y in the code" → `search-code`
- "Locate function Z" → `find-symbol`
- "Search for pattern..." → `grep-pattern`
- "Show me all..." → `search-code`

**Examples:**
```
"Where is the authentication logic?"
"Find all API calls"
"Locate the validateUser function"
```

### 📖 Understanding Code

**Say This** → **Triggers Handler**
- "How does X work?" → `explain-code`
- "Explain Y to me" → `explain-code`
- "What does Z do?" → `explain-code`
- "Walk me through..." → `explain-code`
- "I don't understand..." → `explain-code`

**Examples:**
```
"How does the payment processing work?"
"Explain this useEffect hook"
"Walk me through the login flow"
```

## Complete Phrase Mapping

### Development Tasks

#### Creating New Code
| You Say | Claude Does | Handler |
|---------|-------------|---------|
| "Create a component" | Makes new React/Vue component | `create-component` |
| "Build a service" | Creates service module | `create-component` |
| "Make a new file" | Creates specified file | `create-file` |
| "Add a function" | Implements new function | `create-function` |
| "Implement feature" | Starts feature development | `implement-feature` |

#### Modifying Code
| You Say | Claude Does | Handler |
|---------|-------------|---------|
| "Change X to Y" | Updates specific code | `edit-file` |
| "Update the..." | Modifies existing code | `edit-file` |
| "Refactor this" | Improves code structure | `refactor-code` |
| "Clean up..." | Removes unnecessary code | `cleanup-code` |
| "Optimize..." | Improves performance | `optimize-code` |

#### Working with Git
| You Say | Claude Does | Handler |
|---------|-------------|---------|
| "Commit changes" | Creates git commit | `commit-changes` |
| "Save my work" | Commits with message | `commit-changes` |
| "Create branch" | Makes new git branch | `create-branch` |
| "What changed?" | Shows git status | `check-status` |
| "Show commits" | Lists recent commits | `view-history` |

### Testing & Validation

| You Say | Claude Does | Handler |
|---------|-------------|---------|
| "Test this" | Runs/creates tests | `create-test` |
| "Validate changes" | Verifies functionality | `validate-changes` |
| "Check if working" | Tests implementation | `verify-implementation` |
| "Run tests" | Executes test suite | `run-tests` |
| "Add test coverage" | Creates missing tests | `add-tests` |

### Documentation

| You Say | Claude Does | Handler |
|---------|-------------|---------|
| "Document this" | Adds documentation | `create-docs` |
| "Write README" | Creates README file | `create-readme` |
| "Add comments" | Inserts code comments | `add-comments` |
| "Explain in docs" | Documents functionality | `document-feature` |
| "Create API docs" | Generates API documentation | `api-docs` |

### Task Management

| You Say | Claude Does | Handler |
|---------|-------------|---------|
| "What's next?" | Shows pending tasks | `check-progress` |
| "Mark X as done" | Updates task status | `update-todos` |
| "Plan this out" | Creates task breakdown | `create-todos` |
| "What's left?" | Lists remaining work | `show-remaining` |
| "Break this down" | Decomposes into subtasks | `decompose-task` |

## Trigger Patterns by Category

### Action Verbs That Trigger Handlers

**Create/Make/Build**
- Creates new code or components
- Triggers: `create-component`, `start-new-work`

**Fix/Repair/Resolve**
- Fixes bugs and issues
- Triggers: `fix-bug`, `resolve-issue`

**Find/Search/Locate**
- Searches codebase
- Triggers: `search-code`, `find-symbol`

**Change/Update/Modify**
- Edits existing code
- Triggers: `edit-file`, `update-code`

**Review/Check/Inspect**
- Reviews code quality
- Triggers: `code-review`, `check-quality`

**Test/Verify/Validate**
- Tests functionality
- Triggers: `run-tests`, `validate-changes`

**Document/Explain/Describe**
- Creates documentation
- Triggers: `create-docs`, `explain-code`

### Question Words That Trigger Handlers

| Question Start | Typical Handler | Example |
|----------------|-----------------|---------|
| "How do I...?" | `show-capabilities` | "How do I create a component?" |
| "Why is...?" | `debug-issue` | "Why is the login failing?" |
| "What does...?" | `explain-code` | "What does this function do?" |
| "Where is...?" | `find-symbol` | "Where is the config file?" |
| "Can you...?" | (varies by request) | "Can you refactor this?" |
| "Should I...?" | `best-practices` | "Should I use hooks here?" |

### Emotion/Frustration Triggers

| You Express | Claude Interprets As | Handler |
|-------------|---------------------|---------|
| "This is broken!" | Bug to fix | `fix-bug` |
| "I'm stuck" | Need help debugging | `debug-issue` |
| "This is confusing" | Need explanation | `explain-code` |
| "It's not working" | Issue to investigate | `debug-issue` |
| "I don't know what to do" | Need guidance | `show-capabilities` |

## Magic Phrases

These phrases trigger comprehensive workflows:

### "I want to work on X"
**Effect:** Complete feature setup
- Creates work folder
- Initializes tracking
- Breaks down into tasks
- Starts implementation

### "Fix bug in Y"
**Effect:** Systematic debugging
- Reproduces issue
- Investigates cause
- Implements fix
- Validates solution

### "How does Z work?"
**Effect:** Deep explanation
- Loads relevant code
- Explains architecture
- Details flow
- Answers questions

### "Review my changes"
**Effect:** Comprehensive review
- Analyzes diff
- Checks security
- Reviews performance
- Suggests improvements

### "What's left?"
**Effect:** Progress update
- Shows completed tasks
- Lists remaining work
- Suggests next steps

## Natural Language Variations

Claude understands many ways to say the same thing:

### To Start Work
- "I want to work on..."
- "Let's build..."
- "Time to implement..."
- "Start creating..."
- "Begin development of..."

### To Fix Issues
- "Fix the bug where..."
- "Resolve the problem with..."
- "Debug why..."
- "Something's wrong with..."
- "This is broken:..."

### To Find Code
- "Where is..."
- "Find the..."
- "Locate..."
- "Show me where..."
- "Search for..."

### To Understand
- "How does..."
- "Explain..."
- "What does..."
- "Walk me through..."
- "Help me understand..."

## Special Commands

### Git Shortcuts
- `"gac: message"` → Quick git add, commit
- `"commit: message"` → Commit with specific message
- `"branch: name"` → Create and switch to branch

### Quick Actions
- `"show X"` → Display file or function
- `"run tests"` → Execute test suite
- `"check status"` → Show current state

### Session Management
- `"save progress"` → Update tracking
- `"where are we?"` → Show context
- `"continue"` → Resume previous work

## Pro Tips for Triggers

### 1. Be Direct
Start with action verbs:
- ✅ "Create a button component"
- ❌ "I need a button component"

### 2. Include Context
Specify what you're working on:
- ✅ "Fix the login bug in auth.js"
- ❌ "Fix the bug"

### 3. Use Natural Language
Claude prefers conversation over commands:
- ✅ "Find where users are created"
- ❌ `grep -r "new User"`

### 4. Chain Actions
Combine related requests:
- "Fix the bug, then add tests for it"
- "Refactor this and update the docs"

## Troubleshooting Triggers

### If Handler Doesn't Trigger

**Try These Fixes:**
1. Use more specific action verbs
2. Include file or component names
3. Break complex requests into parts
4. Check similar phrases in this guide

**Example Refinement:**
```
Vague: "Make it better"
Better: "Refactor the user service"
Best: "Refactor the user service to separate auth logic"
```

### Common Misunderstandings

**"Show me X" Ambiguity:**
- File? → Use "Show me the X file"
- Function? → Use "Show me the X function"
- Changes? → Use "Show me what changed"
- How it works? → Use "Explain how X works"

**"Fix X" Context:**
- Bug? → "Fix the bug where X happens"
- Code quality? → "Refactor X for better structure"
- Performance? → "Optimize X for speed"
- Format? → "Format X according to style guide"

## Quick Lookup Table

### Most Common Triggers

| Want to... | Say... |
|------------|--------|
| Start feature | "I want to work on X" |
| Fix bug | "Fix the Y bug" |
| Find code | "Where is Z?" |
| Understand | "How does A work?" |
| Create component | "Create B component" |
| Run tests | "Test C" |
| Save work | "Commit with message D" |
| Check progress | "What's left?" |
| Review code | "Review my changes" |
| Optimize | "Make E faster" |

## Remember

- **Natural language works best** - Talk like you would to a colleague
- **Action words trigger handlers** - Start with verbs
- **Context improves accuracy** - Include relevant details
- **One request at a time** - Break complex tasks down

---

*Back to hub: [Guide Index](../index.md) | Learn workflows: [Common Workflows](../workflows/common.md)*