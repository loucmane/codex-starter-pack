---
id: getting-started
type: user-guide
audience: new-users
skill-level: beginner
title: Getting Started with Claude
description: Essential guide for new users to start using Claude effectively
---

# Getting Started with Claude

## Welcome! 👋

This guide helps you get the most out of Claude for software development. Think of Claude as your AI pair programmer who excels at specific tasks when you communicate clearly.

## Quick Start

### Your First Commands

1. **Start a new feature:**
   ```
   "I want to work on user authentication"
   ```

2. **Fix a bug:**
   ```
   "Fix the login bug where users can't submit the form"
   ```

3. **Understand code:**
   ```
   "How does the payment processing work?"
   ```

4. **Find code:**
   ```
   "Where is the user validation logic?"
   ```

## Core Principles

### 1. Be Specific
❌ **Too vague:** "Fix it"
✅ **Specific:** "Fix the navigation menu not closing on mobile"

### 2. Use Action Words
❌ **Passive:** "The code needs refactoring"
✅ **Active:** "Refactor the user service"

### 3. Provide Context
❌ **No context:** "It's broken"
✅ **With context:** "The login form throws an error when submitting empty fields"

### 4. One Task at a Time
❌ **Multiple tasks:** "Fix the bug and add tests and document it"
✅ **Single task:** "Fix the login bug" (then: "Add tests for login")

## What Claude Does Best

### 🏆 Claude Excels At:

1. **Starting New Work**
   - Creates organized project structure
   - Breaks down features into tasks
   - Sets up proper tracking

2. **Fixing Bugs Systematically**
   - Reproduces issues first
   - Gathers evidence before theorizing
   - Tests fixes thoroughly

3. **Code Search & Navigation**
   - Finds symbols and definitions
   - Locates usage patterns
   - Traces dependencies

4. **Code Understanding**
   - Explains complex logic
   - Documents code flow
   - Clarifies algorithms

5. **Structured Refactoring**
   - Maintains functionality
   - Improves code quality
   - Updates tests

### ⚠️ Claude Needs Help With:

1. **Ambiguous Requests**
   - Be specific about what you want
   - Include file names or function names
   - Describe the expected outcome

2. **Multi-Step Processes**
   - Break down complex tasks
   - Do one thing at a time
   - Verify each step

3. **Project-Specific Knowledge**
   - Provide context about your conventions
   - Mention relevant files
   - Explain custom patterns

## Common First Workflows

### Starting a New Feature

```
You: "I want to work on adding user profiles"
Claude: [Creates work folder, sets up tracking, initializes tasks]
You: "Show me what needs to be done"
Claude: [Shows organized task list]
You: "Let's start with the database schema"
Claude: [Begins implementation]
```

### Fixing Your First Bug

```
You: "Users report the search returns no results"
Claude: [Starts systematic debugging]
You: "The error happens with special characters"
Claude: [Reproduces and investigates]
You: "Found it - the encoding is wrong"
Claude: [Implements proper fix]
```

### Understanding Existing Code

```
You: "How does the authentication middleware work?"
Claude: [Loads relevant code]
Claude: [Explains step by step with line references]
You: "What happens if the token is expired?"
Claude: [Traces that specific path]
```

## Power User Tips for Beginners

### 1. Use Natural Language
Claude understands conversational requests better than commands:
- ✅ "Find where users are created"
- ❌ `grep -r "new User"`

### 2. Leverage Work Tracking
Claude automatically tracks your progress:
- "What's left to do?" - See remaining tasks
- "Mark login as complete" - Update progress
- "Where are we?" - Get status summary

### 3. Provide Examples
When asking for something specific:
```
"Create a button component like the existing Card component"
"Format this similar to our other API endpoints"
```

### 4. Use Claude's Memory
Claude remembers your session:
- "Continue with the auth feature" - Resumes previous work
- "Like we discussed earlier" - References context
- "Use the same pattern" - Applies previous decisions

### 5. Ask for Explanations
Don't hesitate to ask why:
- "Why did you choose that approach?"
- "What are the tradeoffs?"
- "Is there a better way?"

## Communication Patterns

### For Quick Tasks
```
"Change the button color to blue"
"Fix the typo in the error message"
"Add a comment explaining this function"
```

### For Complex Tasks
```
"I need to implement a shopping cart. Let's start by planning it out."
"Help me refactor this module. First, let's understand what it does."
"Debug why the app is slow. Can you analyze the performance?"
```

### For Learning
```
"Explain how React hooks work in this component"
"What's the best practice for error handling here?"
"Show me examples of good test cases"
```

## Getting Unstuck

### When Claude doesn't understand:
1. Rephrase with more detail
2. Provide a specific file or function name
3. Give an example of what you want
4. Break it into smaller steps

### When you're not sure what to do:
- "What can you help me with?"
- "Show me the available commands"
- "What should I work on next?"
- "How do I approach this problem?"

### When something goes wrong:
- "That didn't work, let's try another approach"
- "The error is still happening"
- "Can you explain what went wrong?"
- "Let's debug this step by step"

## Next Steps

Now that you understand the basics:

1. **Try a simple task** - Start with something small like fixing a typo
2. **Learn about ULTRATHINK** - See [Understanding ULTRATHINK](../ultrathink/understanding.md)
3. **Explore workflows** - Check [Common Workflows](../workflows/common.md)
4. **Keep references handy** - Bookmark [Trigger Phrases](../reference/triggers.md)

## Quick Reference Card

**Most Useful Phrases for Beginners:**
- "I want to work on X" - Start new feature
- "Fix the Y bug" - Debug and fix
- "How does Z work?" - Understand code
- "Find where A is defined" - Locate code
- "What's left to do?" - Check progress

Remember: Claude works best when you communicate clearly, stay focused on one task at a time, and provide context!

---

*Continue learning: [Understanding ULTRATHINK](../ultrathink/understanding.md) →*