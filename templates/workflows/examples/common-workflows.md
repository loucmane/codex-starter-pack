---
id: common-development-workflows
type: workflow-component
category: examples
title: Common Development Workflows
dependencies:
  - ../handlers/intent-handlers.md
  - ../patterns/task-management.md
related:
  - ../testing/test-checkpoints.md
version: 1.0.0
status: stable
---

> **Codex Alignment:** Before following these examples in Codex, run `python3 scripts/codex-task plan sync` and update the active tracker so guard checks align with plan compliance (replaces the legacy TodoWrite/TodoRead steps).

# Common Development Workflows

This section shows complete workflows from start to finish, demonstrating how multiple handlers chain together to accomplish real development tasks.

## Building a New Feature

**Scenario**: Add User Authentication to an App

```
User: "I want to work on user authentication"
Codex: [start-new-work] → Creates work folder and tracking
        What aspects of authentication do you want to implement?

User: "Login, logout, and session management"
Codex: [create-todos] → Breaks down into tasks:
        1. Create auth service structure
        2. Implement login functionality  
        3. Implement logout functionality
        4. Add session management
        5. Create auth UI components
        6. Add auth tests
        7. Integrate with existing app

User: "Let's start with the auth service"
Codex: [create-component] → Creates service structure
        Created: src/services/auth.service.js
        Added methods: login(), logout(), getSession()

User: "Add the login implementation"
Codex: [edit-file] → Implements login with:
        - Input validation
        - API communication
        - Token storage
        - Error handling

User: "Test that it works"
Codex: [create-test-checkpoint] → Creates and runs tests
        ✅ All auth service tests passing

User: "Great, commit this"
Codex: [commit-changes] → "feat: add auth service with login implementation"
```

## Fixing a Production Bug

**Scenario**: Users Can't Submit Forms

```
User: "Users report the submit button on the contact form isn't working"
Codex: [fix-bug] → Loads bug-fix-template
        First, I need to reproduce the issue...

User: "It works fine locally but fails in production"
Codex: [debug-issue] → Checks environment differences:
        1. API endpoint configuration
        2. CORS settings
        3. Environment variables
        
        Found it! Production API_URL missing /api prefix

User: "That makes sense! Fix it"
Codex: [edit-file] → Updates .env.production
        Also adding validation to prevent future issues

User: "Test that the fix works"
Codex: [validate-changes] → Creates verification test
        ✅ Test passes with correct URL
        ❌ Test fails with missing /api (as expected)

User: "Perfect, commit and let's deploy"
Codex: [commit-changes] → "fix: add missing /api prefix to production API_URL"
```

## Code Review Workflow

**Scenario**: Review Changes Before PR

```
User: "Review my changes before I create a PR"
Codex: [check-status] → Shows git diff in 4 files
        [code-review] → Loads review template

## Code Review Results

✅ Logic & Correctness
- User CRUD operations correct
- Proper error handling
- Edge cases handled

⚠️ Performance Concerns
- UserList re-renders unnecessarily
- API calls could be batched

🔒 Security Issues
- User input not sanitized
- API keys visible in client
- Missing auth on DELETE

User: "Fix the security issues first"
Codex: [edit-file] → Implements:
        1. Input sanitization
        2. Environment variables for keys
        3. Auth middleware on DELETE

User: "Now optimize the performance"
Codex: [optimize-code] → Applies:
        1. React.memo to UserList
        2. useCallback for handlers
        3. Request batching

User: "Great, review again"
Codex: [code-review] → ✅ All issues addressed
```

## Understanding Legacy Code

**Scenario**: Need to Modify Complex System

```
User: "How does the payment system work?"
Codex: [explain-code] → Analyzes payment system
        [find-symbol] → Locates main functions

## Payment System Overview

1. Entry: processPayment() at processor.js:42
   - Receives payment data
   - Validates card info

2. Validation: validatePayment() at validation.js:15
   - Checks card format
   - Verifies expiry/CVV

3. Gateway: chargeCard() at gateway.js:78
   - Connects to Stripe
   - Handles 3D Secure

4. Response: Back at processor.js:67
   - Updates order status
   - Sends confirmation

User: "Where does it handle failed payments?"
Codex: [find-references] → Shows failure handling:
        - gateway.js:95 - Network failures
        - processor.js:73 - Business logic failures

User: "I need to add PayPal support"
Codex: Based on architecture:
        1. Create paypal-gateway.js
        2. Implement same interface
        3. Add to processor switch
        Want me to start implementing?
```

## Performance Optimization

**Scenario**: Application Running Slowly

```
User: "The dashboard is loading very slowly"
Codex: [debug-issue] → Performance investigation
        [measure-complexity] → Analyzing code

## Performance Analysis

🔴 Critical Issues:
1. Unnecessary Re-renders (Dashboard.jsx:45)
2. 15 Separate API Calls (api/dashboard.js:23)
3. Heavy Computation (calculations.js:67)

User: "Fix the API calls first"
Codex: [optimize-code] → Implements batching
        Before: 15 calls (3.2s)
        After: 3 calls (0.8s)

User: "Now fix the re-rendering"
Codex: [optimize-code] → Applies:
        - React.memo to children
        - useMemo for calculations
        - useCallback for handlers
        Renders: 47 → 3

User: "What's the overall improvement?"
Codex: Summary:
        Load time: 4.8s → 1.2s (75% faster)
        Interaction: 400ms → 50ms (87% faster)
        Memory: 45MB → 28MB (38% reduction)
```

## Test-Driven Development

**Scenario**: Building with TDD

```
User: "Let's build a user profile component using TDD"
Codex: [create-test-checkpoint] → Writes tests first:
        1. Renders user information
        2. Handles missing data
        3. Shows edit button for own profile
        4. Hides edit for others
        5. Updates on data change

User: "Run the tests"
Codex: [run-tests] → ❌ All 5 failing (expected)

User: "Create minimal implementation"
Codex: [create-component] → Basic UserProfile
        [run-tests] → ✅ 3/5 passing

User: "Fix the failing tests"
Codex: [edit-file] → Adds:
        - Null checks
        - useEffect for updates
        [run-tests] → ✅ 5/5 passing!

User: "Refactor to make it cleaner"
Codex: [refactor-code] → Extracts:
        - UserAvatar component
        - useUserProfile hook
        [run-tests] → ✅ Still passing!
```

## Key Workflow Patterns

### 1. Investigation → Implementation → Validation
- First understand (search, explain, analyze)
- Then implement (create, edit, refactor)
- Finally validate (test, review, commit)

### 2. Incremental Progress
- Break large tasks into small steps
- Validate each step before proceeding
- Commit working code frequently

### 3. Context Building
- Start broad, then narrow focus
- Gather evidence before changes
- Document decisions and findings

### 4. Systematic Approach
- Use templates for consistency
- Follow established patterns
- Maintain tracking throughout

## Workflow Success Tips

### Set Clear Goals
- State what you want to achieve
- Define success criteria
- Identify constraints

### Provide Context
- Mention related files
- Explain business requirements
- Share previous decisions

### Iterate and Refine
- Start simple, enhance gradually
- Test frequently
- Refactor when stable

### Track Progress
- Use work tracking system
- Commit meaningful checkpoints
- Document important findings

These workflows show how handlers chain together to accomplish real development tasks efficiently and systematically.