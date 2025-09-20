---
id: code-style-general
type: convention
category: code-style
title: Language-Agnostic Style Rules
applies_to: code
enforcement: required
dependencies: []
version: 1.0.0
status: stable
---

# General Code Style Rules

## Convention
All code, regardless of language, must follow consistent formatting and structural patterns for readability and maintainability.

## Indentation and Spacing

### Indentation
- **Standard**: 2 spaces (never tabs)
- **Consistency**: Same throughout file
- **No mixing**: Never mix spaces and tabs

```javascript
// ✅ Correct - 2 space indentation
function example() {
  if (condition) {
    doSomething();
  }
}

// ❌ Wrong - 4 spaces or tabs
function example() {
    if (condition) {
        doSomething();
    }
}
```

### Line Length
- **Maximum**: 100 characters preferred, 120 absolute max
- **Breaking**: Break at logical points
- **Indentation**: Continued lines indented 2 levels

```javascript
// ✅ Good line breaking
const result = someVeryLongFunctionName(
    firstParameter,
    secondParameter,
    thirdParameter
);

// ❌ Too long
const result = someVeryLongFunctionName(firstParameter, secondParameter, thirdParameter, fourthParameter);
```

## Brace Style

### K&R Style (One True Brace)
```javascript
// ✅ Opening brace on same line
if (condition) {
  doSomething();
} else {
  doSomethingElse();
}

// ❌ Allman style - avoid
if (condition)
{
  doSomething();
}
```

## Whitespace Rules

### Around Operators
```javascript
// ✅ Space around operators
const sum = a + b;
const result = x * y / z;
const isValid = value > 0 && value < 100;

// ❌ No spaces
const sum=a+b;
const result=x*y/z;
```

### After Keywords
```javascript
// ✅ Space after keywords
if (condition) { }
for (let i = 0; i < 10; i++) { }
while (running) { }

// ❌ No space
if(condition) { }
for(let i = 0; i < 10; i++) { }
```

### Function Calls
```javascript
// ✅ No space before parentheses in calls
functionName();
method.call();

// ❌ Space before parentheses
functionName ();
method.call ();
```

## Comments

### Comment Types
```javascript
// ✅ Single-line comment for brief notes

/*
 * ✅ Multi-line comment for longer explanations
 * Each line starts with asterisk aligned
 */

/**
 * ✅ JSDoc comment for documentation
 * @param {string} name - Parameter description
 * @returns {boolean} Return description
 */
```

### Comment Content
```javascript
// ✅ Explain WHY, not WHAT
// Cache result to avoid expensive recalculation
const cached = expensiveOperation();

// ❌ Obvious comment
// Increment counter by 1
counter++;

// ✅ TODO with context
// TODO(john): Optimize for arrays > 1000 items
// FIXME: Handle null case - crashes in production
// NOTE: This assumes data is pre-sorted
```

## Naming Principles

### Descriptive Names
```javascript
// ✅ Clear, descriptive names
const userEmail = 'john@example.com';
const isLoggedIn = true;
const calculateTotalPrice = () => { };

// ❌ Unclear names
const e = 'john@example.com';
const flag = true;
const calc = () => { };
```

### Avoid Abbreviations
```javascript
// ✅ Full words
const temperature = 25;
const maximum = 100;
const userInformation = {};

// ❌ Unclear abbreviations
const temp = 25;
const max = 100;
const usrInfo = {};

// ✅ Acceptable common abbreviations
const url = 'https://example.com';
const api = new ApiClient();
const id = '123';
```

## Code Organization

### Logical Grouping
```javascript
// ✅ Group related code
// User-related functions
function getUser() { }
function updateUser() { }
function deleteUser() { }

// Post-related functions
function getPost() { }
function updatePost() { }
function deletePost() { }

// ❌ Mixed concerns
function getUser() { }
function getPost() { }
function updateUser() { }
function deletePost() { }
```

### Consistent Ordering
```javascript
// ✅ Consistent class member ordering
class Example {
  // 1. Static properties
  static defaultValue = 10;
  
  // 2. Instance properties
  private value: number;
  
  // 3. Constructor
  constructor(value: number) {
    this.value = value;
  }
  
  // 4. Public methods
  public getValue(): number {
    return this.value;
  }
  
  // 5. Private methods
  private validate(): boolean {
    return this.value > 0;
  }
}
```

## Error Handling

### Explicit Error Handling
```javascript
// ✅ Handle errors explicitly
try {
  const result = riskyOperation();
  return result;
} catch (error) {
  console.error('Operation failed:', error);
  return fallbackValue;
}

// ❌ Ignoring errors
try {
  riskyOperation();
} catch (e) {
  // Silent failure
}
```

### Error Messages
```javascript
// ✅ Descriptive error messages
throw new Error(`User ${userId} not found in database`);

// ❌ Vague error messages
throw new Error('Error');
throw new Error('Failed');
```

## Function Design

### Single Responsibility
```javascript
// ✅ One function, one purpose
function validateEmail(email) {
  return emailRegex.test(email);
}

function sendEmail(email, message) {
  // Only sends email
}

// ❌ Multiple responsibilities
function validateAndSendEmail(email, message) {
  if (emailRegex.test(email)) {
    // Validation and sending mixed
    sendEmail(email, message);
  }
}
```

### Function Length
- **Target**: < 20 lines
- **Maximum**: 50 lines
- **Extract**: Helper functions for complex logic

## Package Manager

### Always Use pnpm
```bash
# ✅ CORRECT
pnpm install
pnpm add <package>
pnpm dev

# ❌ WRONG - Never use these
npm install      # Don't use npm
yarn add         # Don't use yarn
```

## Accessibility Standards

### Minimum Touch Targets
```css
/* ✅ All interactive elements must have 44px minimum */
button {
  min-height: 44px;
  min-width: 44px;
}
```

### ARIA Labels
```html
<!-- ✅ Always include ARIA labels for icon buttons -->
<button aria-label="Close menu" onClick={closeMenu}>
  <X size={24} />
</button>
```

## Performance Considerations

### Avoid Premature Optimization
```javascript
// ✅ Write clear code first
const result = items.filter(item => item.active)
                   .map(item => item.value);

// ❌ Don't optimize without measurement
const result = [];
for (let i = 0, len = items.length; i < len; i++) {
  if (items[i].active) {
    result.push(items[i].value);
  }
}
```

## Rationale

### Why These Conventions

1. **Readability**: Consistent style reduces cognitive load
2. **Maintainability**: Predictable code is easier to modify
3. **Team Efficiency**: No debates about style
4. **Tool Support**: Linters can enforce rules
5. **Bug Prevention**: Many rules prevent common errors

### Benefits
- **Faster Reviews**: No style discussions in PRs
- **Easier Onboarding**: New developers learn one style
- **Better Collaboration**: Everyone writes similar code
- **Reduced Errors**: Consistent patterns prevent mistakes
- **Professional Quality**: Clean, consistent codebase