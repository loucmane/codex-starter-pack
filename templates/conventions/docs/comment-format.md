---
id: comment-format
type: convention
category: docs
title: Code Comment Conventions
applies_to: code
enforcement: required
dependencies:
  - documentation-standards
version: 1.0.0
status: stable
---

# Code Comment Format

## Convention
Comments must explain WHY not WHAT, be concise, and follow consistent formatting patterns.

## Comment Principles

### Explain WHY, Not WHAT
```javascript
// ✅ Good - Explains reasoning
// Cache result to avoid expensive recalculation on each render
const memoizedValue = useMemo(() => expensiveCalculation(data), [data]);

// ❌ Bad - States the obvious
// Set user name to 'John'
user.name = 'John';
```

### Add Value
```javascript
// ✅ Good - Provides context
// Using bitwise operation for performance (10x faster than Math.floor)
const integer = ~~decimal;

// ❌ Bad - No value added
// Increment i
i++;
```

### Be Concise
```javascript
// ✅ Good - Brief and clear
// Retry with exponential backoff
await delay(Math.pow(2, attempt) * 1000);

// ❌ Bad - Too verbose
// This function will wait for a certain amount of time
// The time is calculated using exponential backoff
// which means we double the wait time for each retry
// This helps prevent overwhelming the server
await delay(Math.pow(2, attempt) * 1000);
```

## Comment Types

### Single-Line Comments
```javascript
// ✅ Use for brief explanations
const MAX_RETRIES = 3;  // Empirically determined optimal value

// ✅ Use above the line being explained
// Check if user has admin privileges
if (user.role === 'admin') {
  enableAdminFeatures();
}

// ❌ Avoid trailing comments for complex explanations
const result = complexCalculation();  // This calculation takes into account...
```

### Multi-Line Comments
```javascript
/*
 * ✅ Use for longer explanations
 * Each line starts with an asterisk
 * Properly aligned for readability
 */

/*
 * Authentication flow:
 * 1. User submits credentials
 * 2. Validate against database
 * 3. Generate JWT token
 * 4. Return token to client
 */
```

### Documentation Comments (JSDoc)
```javascript
/**
 * ✅ Use for functions, classes, and modules
 * @param {string} userId - The user's unique identifier
 * @returns {Promise<User>} The user object
 */
function getUser(userId) { }
```

## TODO Comments

### Format
```javascript
// TODO(author): Description of task
// TODO(john): Optimize for arrays larger than 1000 items
// TODO(2025-08-15): Remove after migration complete

// FIXME: Critical issue description
// FIXME: Handle null case - causes crash in production

// NOTE: Important information
// NOTE: This assumes input is pre-sorted

// HACK: Temporary solution
// HACK: Workaround for library bug, remove after update

// DEPRECATED: Will be removed
// DEPRECATED: Use newFunction() instead
```

### Requirements
- Always include author or date
- Be specific about the task
- Remove completed TODOs
- Convert FIXME to issues when possible

## Anti-Patterns to Avoid

### Commented-Out Code
```javascript
// ❌ Don't leave commented code
// function oldImplementation() {
//   return 'old';
// }

// ✅ Delete it - version control preserves history
```

### Obvious Comments
```javascript
// ❌ Avoid stating the obvious
// Constructor
constructor() { }

// Return the user name
return user.name;

// Check if x equals 5
if (x === 5) { }
```

### Misleading Comments
```javascript
// ❌ Outdated comment (says email but checks username)
// Validate email format
if (username.length < 3) {
  throw new Error('Invalid username');
}
```

### Noise Comments
```javascript
// ❌ Meaningless comments
// Start of function
function process() {
  // Do the thing
  doThing();
  // End of function
}
```

## Comment Placement

### Above the Code
```javascript
// ✅ Place comment above the code it describes
// Calculate compound interest using the formula
// A = P(1 + r/n)^(nt)
const amount = principal * Math.pow(1 + rate / frequency, frequency * time);
```

### Inline Comments
```javascript
// ✅ Use sparingly for clarification
const mask = 0xFF;  // 8-bit mask
const timeout = 5000;  // 5 seconds in milliseconds
```

### Section Comments
```javascript
// ============================================
// Initialization
// ============================================

// ----------------------------------------
// Helper Functions
// ----------------------------------------

/* ===== Configuration ===== */
```

## Special Comment Formats

### Region Comments (for code folding)
```javascript
// #region Initialization
const config = loadConfig();
const db = connectDatabase();
// #endregion

// #region Event Handlers
function handleClick() { }
function handleSubmit() { }
// #endregion
```

### License Headers
```javascript
/**
 * Copyright (c) 2025 Company Name
 * Licensed under the MIT License
 * See LICENSE file for details
 */
```

### File Headers
```javascript
/**
 * @file User authentication module
 * @author John Doe
 * @since 1.0.0
 * @module auth
 */
```

## Examples

### ✅ Good Comments
```javascript
class RateLimiter {
  constructor() {
    // Use WeakMap to allow garbage collection of unused keys
    this.attempts = new WeakMap();
    
    // 429 is the standard HTTP status for rate limiting
    this.errorCode = 429;
  }
  
  checkLimit(user) {
    // Reset counter at midnight UTC to align with analytics
    if (this.isNewDay()) {
      this.resetCounters();
    }
    
    // Exponential backoff prevents thundering herd problem
    const delay = Math.pow(2, attempts) * 1000;
    
    return delay;
  }
}
```

### ❌ Bad Comments
```javascript
class RateLimiter {
  constructor() {
    // Create a new WeakMap
    this.attempts = new WeakMap();
    
    // Set error code to 429
    this.errorCode = 429;
  }
  
  // This method checks the limit
  checkLimit(user) {
    // Check if it's a new day
    if (this.isNewDay()) {
      // Reset the counters
      this.resetCounters();
    }
    
    // Calculate delay
    const delay = Math.pow(2, attempts) * 1000;
    
    // Return the delay
    return delay;
  }
}
```

## Rationale

### Why These Conventions

1. **Value-Add**: Comments should provide information not obvious from code
2. **Maintenance**: Outdated comments are worse than no comments
3. **Clarity**: Good comments reduce cognitive load
4. **Documentation**: Comments serve as inline documentation
5. **Team Communication**: Comments share knowledge and decisions

### Benefits
- **Faster Understanding**: WHY explanations speed comprehension
- **Reduced Bugs**: Context helps avoid breaking assumptions
- **Knowledge Transfer**: Decisions and reasoning preserved
- **Easier Debugging**: Comments provide debugging context
- **Code Review**: Comments explain non-obvious choices