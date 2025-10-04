# Claude User Guide

## Welcome! 👋

This guide helps you get the most out of Claude for software development. Think of Claude as your AI pair programmer who excels at specific tasks when you communicate clearly.

## 📚 Guide Contents

- [How to Use Claude Effectively](#how-to-use-claude-effectively)
- [Common Search Patterns](#common-search-patterns)
- [If You Want To... Say This!](#if-you-want-to-say-this)
- [Troubleshooting Guide](#troubleshooting-guide)

## 🔗 Quick Links

- **Full handler list** → [REGISTRY.md](REGISTRY.md)
- **See handlers in action** → [templates/workflows/examples/common-workflows.md](templates/workflows/examples/common-workflows.md)
- **Create new handlers** → [BUILDING-BETTER.md#creating-handlers](BUILDING-BETTER.md#creating-handlers)
- **Standards & conventions** → [CONVENTIONS.md](templates/conventions/)

---

## 🧠 Understanding ULTRATHINK

You'll see Claude start responses with something like:
```
Let me ultrathink about this... [S:20250726|W:feature-auth|H:create-component|E:3/"Component created"]
```

This is the ULTRATHINK system ensuring Claude has proper context before acting:
- **S** = Session ID (today's date)
- **W** = Work context (what Claude is working on)
- **H** = Handler (which workflow Claude will use)
- **E** = Evidence (proves handler was read and executed)

### When You'll See VOID
Sometimes you'll see:
```
Let me ultrathink about this... [S:VOID→conventions|W:VOID→workflows|H:VOID→registry|E:searching]
```

This means Claude needs to establish context first. The arrows (→) show where Claude will look to resolve each VOID:
- **S:VOID→conventions** = Need to check/create today's session
- **W:VOID→workflows** = Need to determine work context
- **H:VOID→registry** = Need to find the right handler

This ensures Claude always has the right context for your request!

---

# How to Use Claude Effectively

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

## Common Workflows

### Starting a New Feature

```
You: "I want to work on adding user profiles"
Claude: [Creates work folder, sets up tracking, initializes tasks]
You: "Show me what needs to be done"
Claude: [Shows organized task list]
You: "Let's start with the database schema"
Claude: [Begins implementation]
```

### Fixing a Bug

```
You: "Users report the search returns no results"
Claude: [Starts systematic debugging]
You: "The error happens with special characters"
Claude: [Reproduces and investigates]
You: "Found it - the encoding is wrong"
Claude: [Implements proper fix]
```

### Understanding Code

```
You: "How does the authentication middleware work?"
Claude: [Loads relevant code]
Claude: [Explains step by step with line references]
You: "What happens if the token is expired?"
Claude: [Traces that specific path]
```

### Code Review

```
You: "Review my changes to the checkout process"
Claude: [Examines git diff]
Claude: [Provides categorized feedback]
You: "How can I improve the error handling?"
Claude: [Suggests specific improvements]
```

## Power User Tips

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

## Best Practices Checklist

### ✅ Do:
- Be specific and clear
- Provide context and examples
- Use action-oriented language
- Give feedback on results
- Ask questions when unclear

### ❌ Don't:
- Use vague requests like "make it better"
- Combine multiple unrelated tasks
- Assume Claude knows project-specific details
- Use technical commands instead of natural language
- Skip verification steps

## Example Conversations

### Good Conversation Flow
```
You: "I want to add email validation to the signup form"
Claude: [Acknowledges and prepares]
You: "Show me the current form code"
Claude: [Displays relevant code]
You: "Add validation before the API call"
Claude: [Implements validation]
You: "Test that it works with invalid emails"
Claude: [Creates and runs tests]
You: "Great, commit this change"
Claude: [Commits with proper message]
```

### Learning Together
```
You: "I'm not sure how to structure this feature"
Claude: [Asks clarifying questions]
You: "It needs to handle user preferences"
Claude: [Suggests architecture options]
You: "Option 2 sounds good, let's go with that"
Claude: [Implements chosen approach]
```

## Quick Reference Card

**Most Useful Phrases:**
- "I want to work on X" - Start new feature
- "Fix the Y bug" - Debug and fix
- "How does Z work?" - Understand code
- "Find where A is defined" - Locate code
- "Review my changes" - Code review
- "What's left to do?" - Check progress
- "Create tests for B" - Add testing
- "Refactor C" - Improve code
- "Document D" - Add documentation
- "Commit with message E" - Save work

## Remember

Claude works best when you:
1. **Communicate clearly** - Like talking to a colleague
2. **Stay focused** - One task at a time
3. **Provide context** - Share relevant details
4. **Verify results** - Check the work
5. **Learn together** - Ask questions and iterate

Happy coding! 🚀

---

# Common Search Patterns

## How Users Ask vs What Handlers Exist

This guide maps natural user language to the appropriate handlers, helping both users and the AI find the right functionality quickly.

## By Intent Category

### 🚀 Starting Something New

**Users Say** → **Handler to Use**
- "I want to build a new feature" → `start-new-work`
- "Let's create a login system" → `start-new-work`
- "Time to implement authentication" → `start-new-work`
- "Starting fresh on the API" → `start-new-work`
- "Beginning work on dark mode" → `start-new-work`

### 🔧 Fixing Problems

**Users Say** → **Handler to Use**
- "The login is broken" → `fix-bug`
- "Navigation isn't working" → `fix-bug`
- "Users can't submit the form" → `fix-bug`
- "There's a bug in checkout" → `fix-bug`
- "Something's wrong with search" → `fix-bug`

### 🔍 Finding Things

**Users Say** → **Handler to Use**
- "Where is the auth logic?" → `find-symbol` or `search-code`
- "Show me the login function" → `find-symbol`
- "Find all API calls" → `grep-pattern`
- "What files use UserContext?" → `find-references`
- "Look for error handling" → `search-code`

### 🧐 Understanding Code

**Users Say** → **Handler to Use**
- "How does authentication work?" → `explain-code`
- "What does this useEffect do?" → `explain-code`
- "Explain the payment flow" → `explain-code`
- "Walk me through this algorithm" → `explain-code`
- "I don't understand this function" → `explain-code`

### 📝 Making Changes

**Users Say** → **Handler to Use**
- "Change the button color to blue" → `edit-file`
- "Update the API endpoint" → `edit-file`
- "Add a new field to the form" → `edit-file`
- "Remove the old comments" → `edit-file`
- "Fix the typo in the message" → `edit-file`

### 🏗️ Creating New Code

**Users Say** → **Handler to Use**
- "Create a new Button component" → `create-component`
- "Make a user service" → `create-component`
- "Build a custom hook for auth" → `create-component`
- "Add a utility function" → `create-component`
- "New API endpoint needed" → `create-component`

### 🧹 Cleaning Up Code

**Users Say** → **Handler to Use**
- "This code is messy" → `refactor-code`
- "Clean up the auth service" → `refactor-code`
- "Simplify this component" → `refactor-code`
- "This needs better structure" → `refactor-code`
- "Make this more maintainable" → `refactor-code`

### 🐛 Debugging Issues

**Users Say** → **Handler to Use**
- "Why is this failing?" → `debug-issue`
- "What's causing the error?" → `debug-issue`
- "The app crashes on login" → `debug-issue`
- "Track down the memory leak" → `debug-issue`
- "Figure out why it's slow" → `debug-issue` or `optimize-code`

### ✅ Managing Tasks

**Users Say** → **Handler to Use**
- "What should I do next?" → `check-progress`
- "Mark login as complete" → `update-todos`
- "Plan out the feature" → `create-todos`
- "What's left to do?" → `check-progress`
- "Break this down into steps" → `create-todos`

### 💾 Version Control

**Users Say** → **Handler to Use**
- "Save my changes" → `commit-changes`
- "What did I change?" → `check-status`
- "Commit with 'fixed login bug'" → `commit-changes`
- "Create a feature branch" → `create-branch`
- "Show recent commits" → `view-history`

### 🧪 Testing

**Users Say** → **Handler to Use**
- "Test the login flow" → `create-test-checkpoint`
- "Add tests for the API" → `create-test-checkpoint`
- "Make sure auth works" → `validate-changes`
- "Check if my fix works" → `validate-changes`
- "Run the test suite" → `run-tests`

### 📚 Documentation

**Users Say** → **Handler to Use**
- "Document the API" → `create-docs`
- "Write a README" → `create-docs`
- "Add comments to this" → `create-docs`
- "Explain how to use this" → `create-docs`
- "Create setup instructions" → `create-docs`

### 🔍 Code Review

**Users Say** → **Handler to Use**
- "Review my changes" → `code-review`
- "Check my PR" → `code-review`
- "Is this code good?" → `code-review`
- "Give me feedback" → `code-review`
- "Audit the security" → `code-review`

### ⚡ Performance

**Users Say** → **Handler to Use**
- "This is too slow" → `optimize-code`
- "Speed up the search" → `optimize-code`
- "Improve performance" → `optimize-code`
- "Reduce load time" → `optimize-code`
- "Make it faster" → `optimize-code`

## Common Confusion Points

### "Show me X" - Multiple Handlers Apply
- If X is a file → `read-file`
- If X is a symbol/function → `find-symbol`
- If X is changes → `check-status`
- If X is how something works → `explain-code`

### "Fix X" - Context Matters
- If X is broken → `fix-bug`
- If X is messy code → `refactor-code`
- If X is formatting → `format-code`
- If X is performance → `optimize-code`

### "Check X" - Many Meanings
- Check if working → `validate-changes`
- Check code quality → `code-review`
- Check naming → `check-naming`
- Check git status → `check-status`

## Natural Language Patterns

### Questions That Trigger Handlers
- "How do I...?" → Usually needs `show-capabilities`
- "Why is...?" → Usually needs `debug-issue`
- "What does...?" → Usually needs `explain-code`
- "Where is...?" → Usually needs `find-symbol`
- "Can you...?" → Depends on request

### Action Words and Their Handlers
- **Create/Make/Build** → `create-component` or `start-new-work`
- **Fix/Repair/Resolve** → `fix-bug`
- **Find/Search/Locate** → `search-code` or `find-symbol`
- **Change/Update/Modify** → `edit-file`
- **Review/Check/Inspect** → `code-review`
- **Test/Verify/Validate** → `validate-changes`
- **Document/Explain/Describe** → `create-docs` or `explain-code`

### Emotion/Frustration Mapping
- "This is broken!" → `fix-bug`
- "I'm stuck" → `debug-issue` or `show-capabilities`
- "This is confusing" → `explain-code`
- "It's not working" → `fix-bug` or `debug-issue`
- "I don't know what to do" → `show-capabilities` or `check-progress`

## Quick Reference Card

### Most Common Requests
1. **"Fix the bug"** → `fix-bug`
2. **"How does this work?"** → `explain-code`
3. **"Find where X is"** → `find-symbol`
4. **"Make it faster"** → `optimize-code`
5. **"Review my code"** → `code-review`
6. **"What's next?"** → `check-progress`
7. **"Save changes"** → `commit-changes`
8. **"Create a component"** → `create-component`
9. **"Run tests"** → `run-tests`
10. **"Start new feature"** → `start-new-work`

## Pro Tips

1. **Be specific** - "Fix login bug" better than "fix it"
2. **Include context** - "Review my auth changes" better than "review"
3. **Use action verbs** - "Create", "Fix", "Find", "Explain"
4. **Ask directly** - "How does auth work?" triggers handlers better than "I'm curious about auth"

## If Handler Not Found

When the AI can't find a handler, try:
1. Rephrase with action verbs
2. Be more specific about what you want
3. Use words from the categories above
4. Ask "What can you do?" to see capabilities
5. Break complex requests into smaller parts

---

# If You Want To... Say This!

A quick reference guide mapping what you want to do to exactly what to say to Claude.

## 🚀 Development Tasks

### If you want to... **Start a new feature**
Say:
- ✅ "I want to work on user authentication"
- ✅ "Let's build a shopping cart"
- ✅ "Start working on the payment system"

### If you want to... **Create a component/module**
Say:
- ✅ "Create a new Button component"
- ✅ "Build a user service module"
- ✅ "Make a custom hook for data fetching"

### If you want to... **Implement functionality**
Say:
- ✅ "Implement user login"
- ✅ "Add search functionality"
- ✅ "Create API endpoints for products"

## 🐛 Fixing Problems

### If you want to... **Fix a bug**
Say:
- ✅ "Fix the login bug"
- ✅ "The navbar is broken"
- ✅ "Resolve issue with form submission"

### If you want to... **Debug an issue**
Say:
- ✅ "Debug why login fails"
- ✅ "Why is the page loading slowly?"
- ✅ "Find the problem with data fetching"

### If you want to... **Understand an error**
Say:
- ✅ "Explain this error message"
- ✅ "What does 'undefined is not a function' mean here?"
- ✅ "Debug this stack trace"

## 🔍 Finding Code

### If you want to... **Find where something is defined**
Say:
- ✅ "Where is the login function?"
- ✅ "Find the UserContext definition"
- ✅ "Locate the API configuration"

### If you want to... **Search for patterns**
Say:
- ✅ "Find all console.log statements"
- ✅ "Search for TODO comments"
- ✅ "Look for error handling patterns"

### If you want to... **See what uses something**
Say:
- ✅ "What uses the auth service?"
- ✅ "Find references to UserContext"
- ✅ "Who calls the validateUser function?"

## 📖 Understanding Code

### If you want to... **Understand how something works**
Say:
- ✅ "How does the authentication work?"
- ✅ "Explain this useEffect hook"
- ✅ "What does the payment processor do?"

### If you want to... **Get a code walkthrough**
Say:
- ✅ "Walk me through the login flow"
- ✅ "Explain the data processing pipeline"
- ✅ "How does the search algorithm work?"

## ✏️ Making Changes

### If you want to... **Edit code**
Say:
- ✅ "Change the button color to blue"
- ✅ "Update the API endpoint to /api/v2"
- ✅ "Fix the typo in the error message"

### If you want to... **Refactor code**
Say:
- ✅ "Refactor the auth service"
- ✅ "Clean up this messy component"
- ✅ "Improve the code structure"

### If you want to... **Optimize performance**
Say:
- ✅ "Optimize the search function"
- ✅ "Make the dashboard load faster"
- ✅ "Improve API response time"

## 📋 Task Management

### If you want to... **Plan your work**
Say:
- ✅ "Plan out the user authentication feature"
- ✅ "Break down the payment system"
- ✅ "Create tasks for the migration"

### If you want to... **Check your progress**
Say:
- ✅ "Where are we?"
- ✅ "What's left to do?"
- ✅ "Show progress on authentication"

### If you want to... **Update task status**
Say:
- ✅ "Mark login implementation as done"
- ✅ "The API integration is complete"
- ✅ "Update task: tests are finished"

## 💾 Git Operations

### If you want to... **Save your work**
Say:
- ✅ "Commit with message 'Add user login'"
- ✅ "Save changes: fixed navigation bug"
- ✅ "gac: implement search feature"

### If you want to... **Check what changed**
Say:
- ✅ "What's changed?"
- ✅ "Show git status"
- ✅ "What files did I modify?"

### If you want to... **Work on a branch**
Say:
- ✅ "Create branch for user-auth"
- ✅ "New branch: feature/payment"
- ✅ "Switch to develop branch"

## 🧪 Testing

### If you want to... **Create tests**
Say:
- ✅ "Create tests for login"
- ✅ "Test the user service"
- ✅ "Add test coverage for auth"

### If you want to... **Run tests**
Say:
- ✅ "Run the test suite"
- ✅ "Execute unit tests"
- ✅ "Test the application"

### If you want to... **Validate your work**
Say:
- ✅ "Verify the login works"
- ✅ "Validate my changes"
- ✅ "Confirm the fix works"

## 📚 Documentation

### If you want to... **Document code**
Say:
- ✅ "Document the API endpoints"
- ✅ "Write docs for the auth system"
- ✅ "Create a README for this module"

### If you want to... **Add comments**
Say:
- ✅ "Add comments to this function"
- ✅ "Document what this code does"
- ✅ "Explain this algorithm in comments"

## 👀 Code Review

### If you want to... **Get code reviewed**
Say:
- ✅ "Review my changes"
- ✅ "Check this pull request"
- ✅ "Review the auth implementation"

### If you want to... **Check code quality**
Say:
- ✅ "Is this code following best practices?"
- ✅ "Check for security issues"
- ✅ "Review for performance problems"

## 🔧 Quick Actions

### If you want to... **See a file**
Say:
- ✅ "Show me package.json"
- ✅ "What's in the config file?"
- ✅ "Display the login component"

### If you want to... **Create a file**
Say:
- ✅ "Create a new file: utils/validation.js"
- ✅ "Make a config.json file"
- ✅ "New component: Button.tsx"

### If you want to... **Delete something**
Say:
- ✅ "Remove the old login.js"
- ✅ "Delete unused imports"
- ✅ "Get rid of debug code"

## 💡 Getting Help

### If you want to... **Know what Claude can do**
Say:
- ✅ "What can you do?"
- ✅ "Show capabilities"
- ✅ "Help"

### If you want to... **Start fresh**
Say:
- ✅ "Let's start"
- ✅ "Begin new session"
- ✅ "Start today's work"

### If you want to... **Continue previous work**
Say:
- ✅ "Continue with authentication"
- ✅ "Back to the payment feature"
- ✅ "Resume where we left off"

## 🎯 Pro Tips

1. **Be Direct** - Say what you want, not what you don't want
2. **Include Context** - "Fix login bug" better than "fix bug"
3. **Use Action Words** - Start with verbs like Create, Fix, Find, Show
4. **One Thing at a Time** - Break complex requests into steps

## 🚫 What NOT to Say

### Instead of... **Vague requests**
❌ "Make it better"
✅ "Optimize the search performance"

### Instead of... **Multiple requests**
❌ "Fix the bug and add tests and document it"
✅ Say each separately:
- "Fix the login bug"
- "Create tests for login"
- "Document the login flow"

### Instead of... **Unclear references**
❌ "Fix that thing we talked about"
✅ "Fix the navigation menu bug"

### Instead of... **Passive language**
❌ "The code needs to be refactored"
✅ "Refactor the user service"

## 🎪 Magic Phrases

These phrases trigger powerful workflows:

- **"I want to work on X"** - Sets up everything for a new feature
- **"Fix bug in Y"** - Systematic debugging process
- **"How does Z work?"** - Deep code explanation
- **"Review my changes"** - Comprehensive code review
- **"What's left?"** - Shows your progress and next steps

Remember: Claude responds best to clear, action-oriented requests!

---

# Troubleshooting Guide

## When Things Don't Work as Expected

This guide helps you resolve common issues when working with Claude.

## Quick Fixes for Common Problems

### 🔴 "Claude doesn't understand my request"

**Symptoms:**
- Claude asks for clarification repeatedly
- Wrong handler triggered
- Unexpected response

**Solutions:**
1. **Be more specific**
   - ❌ "Fix it" 
   - ✅ "Fix the login button not responding to clicks"

2. **Include context**
   - ❌ "The error" 
   - ✅ "The 'undefined is not a function' error in auth.js:45"

3. **Use action words**
   - ❌ "The code needs work"
   - ✅ "Refactor the payment service"

4. **Try alternative phrasing**
   - Instead of: "Make it work"
   - Try: "Debug why the form submission fails"

### 🔴 "Claude can't find my code"

**Symptoms:**
- "File not found" errors
- Can't locate symbols
- Wrong files being read

**Solutions:**
1. **Provide exact file paths**
   ```
   "Find the login function in src/auth/login.js"
   ```

2. **Give unique identifiers**
   ```
   "Find the validateUser function" (not just "validate")
   ```

3. **Describe the location**
   ```
   "In the auth module, find where tokens are stored"
   ```

4. **Use the right search terms**
   ```
   "Search for 'localStorage.setItem'" (exact string)
   ```

### 🔴 "Claude makes changes I didn't want"

**Symptoms:**
- Unexpected file modifications
- Wrong code changes
- Unwanted deletions

**Solutions:**
1. **Preview before applying**
   ```
   You: "Show me what changes you'll make first"
   ```

2. **Be explicit about scope**
   ```
   "Only change the color, don't touch the functionality"
   ```

3. **Use git for safety**
   ```
   You: "Create a branch before making changes"
   ```

4. **Specify what NOT to do**
   ```
   "Update the API call but keep the error handling as is"
   ```

### 🔴 "Tests are failing after changes"

**Symptoms:**
- Previously passing tests now fail
- New errors appear
- Functionality broken

**Solutions:**
1. **Run tests before changes**
   ```
   You: "First run the existing tests"
   ```

2. **Make incremental changes**
   ```
   You: "Let's change one function at a time and test"
   ```

3. **Check test assumptions**
   ```
   You: "Do the tests expect the old behavior?"
   ```

4. **Update tests with code**
   ```
   You: "Update both the code and its tests"
   ```

## Handler-Specific Troubleshooting

### start-new-work Not Creating Folder

**Problem:** Work folder not created
**Solution:** 
```
You: "Create work folder for user-authentication feature"
# More explicit about what you want
```

### fix-bug Not Finding Issue

**Problem:** Can't reproduce bug
**Solution:**
```
You: "The bug happens when users click submit with empty email field"
# Provide exact reproduction steps
```

### search-code Returns Too Many Results

**Problem:** Too many matches
**Solution:**
```
You: "Find where user.save() is called in the auth module only"
# Narrow the search scope
```

### commit-changes Has Wrong Message

**Problem:** Commit message doesn't match conventions
**Solution:**
```
You: "Commit with message: 'fix: resolve login validation error'"
# Provide exact message format
```

## Common Error Messages

### "File has not been read yet"

**Meaning:** Claude tried to edit a file without reading it first
**Fix:**
```
You: "First read the config.js file, then update the API_URL"
```

### "No handler found for request"

**Meaning:** Your request doesn't match any handler triggers
**Fix:**
```
You: "Show me what commands are available"
# Then rephrase using suggested patterns
```

### "Cannot find symbol"

**Meaning:** The code element doesn't exist or name is wrong
**Fix:**
```
You: "List all functions in the auth service"
# Find the correct name
```

### "Multiple matches found"

**Meaning:** Search term is too generic
**Fix:**
```
You: "Find the login function in UserService class specifically"
```

## Workflow Issues

### Getting Stuck in a Loop

**Symptoms:**
- Same error repeatedly
- No progress being made
- Circular dependencies

**Solutions:**
1. **Break the cycle**
   ```
   You: "Let's try a different approach"
   ```

2. **Simplify the problem**
   ```
   You: "Just focus on getting the basic version working"
   ```

3. **Skip and return**
   ```
   You: "Mark this as blocked and move to the next task"
   ```

### Lost Context

**Symptoms:**
- Claude forgets previous work
- Repeating already-done tasks
- Missing important details

**Solutions:**
1. **Summarize progress**
   ```
   You: "What have we completed so far?"
   ```

2. **Restore from tracking**
   ```
   You: "Check the work folder for our progress"
   ```

3. **Provide reminders**
   ```
   You: "Remember, we decided to use the singleton pattern"
   ```

### Overwhelming Complexity

**Symptoms:**
- Task too large
- Too many dependencies
- Unclear requirements

**Solutions:**
1. **Decompose the problem**
   ```
   You: "Let's break this into smaller tasks"
   ```

2. **Focus on one aspect**
   ```
   You: "Just implement the data fetching part first"
   ```

3. **Create a plan**
   ```
   You: "Plan out the implementation steps before coding"
   ```

## Performance Issues

### Slow Responses

**Possible Causes:**
- Large file analysis
- Complex searches
- Multiple operations

**Solutions:**
1. Be specific about what to analyze
2. Limit search scope
3. Do operations sequentially

### Context Limit Warnings

**Symptoms:**
- "Approaching context limit"
- Truncated responses
- Missing information

**Solutions:**
1. **Start fresh**
   ```
   You: "Save our progress and let's start a new session"
   ```

2. **Focus on essentials**
   ```
   You: "Just show the relevant function, not the whole file"
   ```

## Best Practices to Avoid Issues

### 1. Clear Communication
- State your goal upfront
- Provide specific examples
- Confirm understanding before proceeding

### 2. Incremental Progress
- Make small changes
- Test frequently
- Commit working code

### 3. Use Safety Nets
- Work in branches
- Keep backups
- Review changes before applying

### 4. Provide Feedback
- Tell Claude what worked
- Correct misunderstandings immediately
- Guide toward the solution you want

## Getting Help

### When to Start Over
- After 3+ failed attempts
- When context is corrupted
- When approach is fundamentally wrong

### How to Reset
```
You: "Let's start fresh. I want to [clear goal statement]"
```

### Asking for Alternatives
```
You: "This approach isn't working. What other ways can we solve this?"
```

### Clarifying Capabilities
```
You: "Can you help with [specific task]?"
You: "What's the best way to [achieve goal]?"
```

## Emergency Commands

### Stop Current Operation
```
"Stop, let's not make those changes"
```

### Revert Changes
```
"Undo the last edit"
"Restore the original version"
```

### Get Status
```
"What did we just change?"
"Show me the current state"
```

### Save Progress
```
"Save our current progress before continuing"
"Create a checkpoint here"
```

## Prevention Tips

1. **Always verify before applying**
   - Review changes
   - Run tests
   - Check dependencies

2. **Communicate clearly**
   - One task at a time
   - Specific file/function names
   - Expected outcomes

3. **Use Claude's strengths**
   - Let it handle systematic tasks
   - Provide context for decisions
   - Ask for explanations

4. **Work with version control**
   - Commit frequently
   - Use branches for experiments
   - Review diffs before committing

Remember: Most issues can be resolved by being more specific, providing context, and breaking complex tasks into smaller steps.

---

## 🔗 Cross-References

- **Add new handlers?** → See [BUILDING-BETTER.md#creating-handlers](BUILDING-BETTER.md#creating-handlers)
- **See all handlers?** → Browse [REGISTRY.md](REGISTRY.md)
- **Common workflows?** → Check [templates/workflows/examples/common-workflows.md](templates/workflows/examples/common-workflows.md)
- **Standards to follow?** → Read [CONVENTIONS.md](templates/conventions/)
- **Improve the system?** → Visit [BUILDING-BETTER.md](templates/integration/)

## 🏷️ Search Keywords

[help, start, new, learn, howto, tutorial, guide, user, documentation, troubleshooting, patterns, search, fix, debug, error, problem, issue]