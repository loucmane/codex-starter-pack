---
id: common-workflows
type: user-guide
audience: developers
skill-level: intermediate
title: Common Development Workflows
description: Real-world examples of Claude in action for typical development tasks
---

# Common Development Workflows

This guide shows you how to work with Claude on real development tasks, with complete conversation flows and expected outcomes.

## Starting a New Feature

### Complete Workflow Example

```
You: "I want to work on adding user profiles to the app"

Claude: Let me ultrathink about this... [S:20250730|W:user-profiles|H:start-new-work|E:5/"Work folder created"]

[Creates folder structure]
/docs/ai/work-tracking/active/20250730-user-profiles-ACTIVE/
  - TRACKER.md (progress tracking)
  - TODO.md (task breakdown)
  - HANDOFF.md (context documentation)

You: "Show me what needs to be done"

Claude: [Displays organized task list from TODO.md]
- [ ] Design user profile schema
- [ ] Create profile component
- [ ] Add profile API endpoints
- [ ] Implement profile editing
- [ ] Add profile picture upload
- [ ] Write tests

You: "Let's start with the database schema"

Claude: [Begins implementation with schema design]
```

### What Happens Behind the Scenes
1. Claude creates organized work folder
2. Breaks down feature into manageable tasks
3. Sets up tracking documents
4. Maintains context throughout development

## Fixing a Bug

### Systematic Debugging Example

```
You: "Users report the search feature returns no results for queries with special characters"

Claude: Let me ultrathink about this... [S:20250730|W:search-bug|H:fix-bug|E:4/"Bug reproduced"]

[Step 1: Reproduce]
Testing search with "user@example.com"...
Confirmed: Returns 0 results when @ symbol present

You: "It should find email addresses"

Claude: [Step 2: Investigate]
Found issue in searchService.js:
- Query not properly escaped for special characters
- Regex pattern treats @ as literal

[Step 3: Fix]
Implementing fix to escape special characters...

You: "Test that it works now"

Claude: [Step 4: Validate]
✓ Search for "user@example.com" returns 3 results
✓ Search for "test+tag" returns 2 results
✓ All existing tests still pass
```

### Bug Fix Pattern
1. **Reproduce** - Confirm the issue exists
2. **Investigate** - Find root cause with evidence
3. **Fix** - Implement targeted solution
4. **Validate** - Test fix doesn't break anything

## Understanding Complex Code

### Code Explanation Example

```
You: "How does the authentication middleware work?"

Claude: Let me ultrathink about this... [S:20250730|W:understanding|H:explain-code|E:3/"Code explained"]

[Loads middleware/auth.js]

The authentication middleware works in 3 stages:

1. **Token Extraction** (lines 5-12)
   - Checks for token in Authorization header
   - Falls back to cookie if no header
   - Returns 401 if no token found

2. **Token Validation** (lines 14-25)
   - Verifies JWT signature
   - Checks expiration time
   - Extracts user ID from payload

3. **User Loading** (lines 27-35)
   - Fetches user from database
   - Attaches to request object
   - Proceeds to next middleware

You: "What happens if the token is expired?"

Claude: When token is expired (line 18):
- JWT.verify() throws 'TokenExpiredError'
- Caught in catch block (line 23)
- Returns 401 with message "Token expired"
- Client should refresh token or re-login
```

### Understanding Pattern
1. Load relevant code
2. Explain high-level flow
3. Detail each component
4. Answer specific questions
5. Provide line references

## Code Review Process

### Review Workflow Example

```
You: "Review my changes to the checkout process"

Claude: Let me ultrathink about this... [S:20250730|W:code-review|H:review-changes|E:4/"Review complete"]

[Examining git diff...]

## Code Review Summary

### ✅ Good Changes
- Improved error handling in payment processing
- Added input validation for credit card
- Better user feedback on failures

### ⚠️ Suggestions
1. **Security Issue** (checkout.js:45)
   - Don't log full credit card number
   - Suggestion: Log only last 4 digits

2. **Performance** (checkout.js:78)
   - Multiple database calls could be batched
   - Suggestion: Use transaction for atomicity

3. **Code Style** (checkout.js:92)
   - Magic number 3 for retry attempts
   - Suggestion: Extract to constant MAX_RETRIES

You: "Fix the security issue"

Claude: [Updates logging to mask sensitive data]
```

### Review Categories
- **Security** - Vulnerabilities and risks
- **Performance** - Speed and efficiency
- **Maintainability** - Code clarity and structure
- **Best Practices** - Industry standards
- **Testing** - Coverage and edge cases

## Creating Components

### Component Creation Example

```
You: "Create a UserAvatar component that shows profile picture with fallback to initials"

Claude: Let me ultrathink about this... [S:20250730|W:components|H:create-component|E:3/"Component created"]

[Creates components/UserAvatar.tsx]

Features implemented:
- Shows image if avatarUrl provided
- Falls back to initials from name
- Configurable size (sm, md, lg)
- Loading and error states
- Click handler for profile navigation

You: "Add a status indicator for online/offline"

Claude: [Enhances component with status dot]
- Green dot for online
- Gray dot for offline
- Pulsing animation for "active now"
```

### Component Pattern
1. Create file in correct location
2. Implement core functionality
3. Add props interface/types
4. Include basic styling
5. Export from index

## Test Development

### Test Creation Example

```
You: "Create tests for the login functionality"

Claude: Let me ultrathink about this... [S:20250730|W:testing|H:create-tests|E:4/"Tests created"]

[Creates auth.test.js]

Test cases covered:
1. ✓ Successful login with valid credentials
2. ✓ Fails with incorrect password
3. ✓ Fails with non-existent user
4. ✓ Handles network errors gracefully
5. ✓ Stores token after successful login
6. ✓ Redirects to dashboard after login

You: "Add a test for remember me functionality"

Claude: [Adds test case for persistent sessions]
```

### Testing Pattern
1. Unit tests for functions
2. Integration tests for workflows
3. Edge cases and error conditions
4. Mock external dependencies
5. Clear test descriptions

## Refactoring Code

### Refactoring Example

```
You: "This UserService class is getting too large, help me refactor it"

Claude: Let me ultrathink about this... [S:20250730|W:refactoring|H:refactor-code|E:5/"Code refactored"]

Analysis of UserService (450 lines):
- Mixed responsibilities: auth, profile, settings
- Suggestion: Split into 3 services

Refactoring plan:
1. AuthService - login, logout, tokens (120 lines)
2. ProfileService - CRUD operations (180 lines)
3. SettingsService - preferences (150 lines)

You: "Yes, let's do that separation"

Claude: [Creates three new service files]
[Updates imports across codebase]
[Maintains backward compatibility]
```

### Refactoring Principles
1. Identify code smells
2. Propose improvement plan
3. Maintain functionality
4. Update all references
5. Test after changes

## Git Workflow

### Commit Process Example

```
You: "I've finished the login feature, commit these changes"

Claude: Let me ultrathink about this... [S:20250730|W:git|H:commit-changes|E:3/"Changes committed"]

Files changed:
- src/auth/login.js
- src/auth/login.test.js
- src/components/LoginForm.tsx

Commit message:
"feat: implement user login with JWT authentication

- Add login form component with validation
- Implement JWT token generation and validation
- Add comprehensive test coverage
- Store tokens securely in httpOnly cookies"

You: "Push to feature branch"

Claude: [Creates and pushes to feature/user-login branch]
```

### Git Best Practices
1. Descriptive commit messages
2. Logical commit grouping
3. Feature branches for new work
4. Regular commits for progress
5. Clean history maintenance

## Performance Optimization

### Optimization Example

```
You: "The dashboard is loading too slowly"

Claude: Let me ultrathink about this... [S:20250730|W:performance|H:optimize-code|E:4/"Performance improved"]

Performance Analysis:
1. Initial load: 3.2 seconds
2. Main bottleneck: 15 API calls on mount

Optimizations implemented:
1. Batch API calls (15 → 3 calls)
2. Add request caching
3. Lazy load heavy components
4. Implement virtual scrolling for lists

Result: Load time reduced to 0.8 seconds

You: "Can we optimize it further?"

Claude: Additional optimizations:
- Implement service worker for offline caching
- Use CDN for static assets
- Add progressive loading for images
```

## Common Patterns Summary

### Development Flow
1. **Plan** → Break down into tasks
2. **Implement** → Follow TDD approach
3. **Test** → Verify functionality
4. **Review** → Check quality
5. **Deploy** → Commit and push

### Problem-Solving Flow
1. **Reproduce** → Confirm issue
2. **Investigate** → Find root cause
3. **Fix** → Implement solution
4. **Validate** → Test thoroughly
5. **Document** → Record solution

### Learning Flow
1. **Explore** → Understand current code
2. **Explain** → Get clarification
3. **Modify** → Make changes
4. **Verify** → Check understanding

## Tips for Smooth Workflows

1. **Be specific** about what you want
2. **Provide context** when switching tasks
3. **Verify changes** before committing
4. **Ask questions** when unclear
5. **Break complex tasks** into steps

---

*Next: Learn specific trigger phrases in [Trigger Phrases](../reference/triggers.md) →*