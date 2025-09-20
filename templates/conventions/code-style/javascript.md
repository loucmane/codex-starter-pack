---
id: code-style-javascript
type: convention
category: code-style
title: JavaScript Specific Conventions
applies_to: code
enforcement: required
dependencies:
  - code-style/general
version: 1.0.0
status: stable
---

# JavaScript Code Style Conventions

## Convention
JavaScript code must follow modern ES6+ standards with consistent formatting and patterns.

## Syntax Preferences

### Variable Declarations
```javascript
// ✅ Use const by default
const userName = 'John';
const items = [];

// ✅ Use let when reassignment needed
let counter = 0;
counter++;

// ❌ Never use var
var oldStyle = 'avoid';  // Don't use var
```

### Arrow Functions vs Regular Functions
```javascript
// ✅ Arrow functions for callbacks and short functions
const doubled = numbers.map(n => n * 2);
const handleClick = () => console.log('clicked');

// ✅ Regular functions for methods and when 'this' is needed
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

const obj = {
  method() {  // Method shorthand
    return this.value;
  }
};
```

### Template Literals
```javascript
// ✅ Use template literals for string interpolation
const message = `Hello, ${userName}!`;
const multiline = `
  This is a
  multiline string
`;

// ❌ Avoid string concatenation
const badMessage = 'Hello, ' + userName + '!';  // Avoid
```

## Destructuring

### Object Destructuring
```javascript
// ✅ Destructure objects when possible
const { name, email, age } = user;
const { data: userData, error } = response;

// ✅ In function parameters
function greetUser({ name, title = 'User' }) {
  return `Hello, ${title} ${name}`;
}

// ❌ Avoid repetitive property access
const name = user.name;  // Use destructuring instead
const email = user.email;
```

### Array Destructuring
```javascript
// ✅ Destructure arrays
const [first, second, ...rest] = items;
const [x, y] = coordinates;

// ✅ Swap variables
[a, b] = [b, a];

// ✅ Skip elements
const [, , third] = items;
```

## Spread and Rest

### Spread Operator
```javascript
// ✅ Array spreading
const combined = [...array1, ...array2];
const copy = [...original];

// ✅ Object spreading
const updated = { ...user, name: 'New Name' };
const merged = { ...defaults, ...options };

// ❌ Avoid Object.assign for simple cases
const bad = Object.assign({}, user, { name: 'New' });  // Use spread
```

### Rest Parameters
```javascript
// ✅ Use rest parameters
function sum(...numbers) {
  return numbers.reduce((a, b) => a + b, 0);
}

// ❌ Avoid arguments object
function oldSum() {
  return Array.from(arguments).reduce((a, b) => a + b, 0);  // Avoid
}
```

## Async/Await

### Async Functions
```javascript
// ✅ Use async/await for asynchronous code
async function fetchUserData(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}

// ✅ Parallel async operations
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts()
]);

// ❌ Avoid promise chains when possible
fetch('/api/users')
  .then(res => res.json())
  .then(data => console.log(data))  // Use async/await instead
  .catch(err => console.error(err));
```

## Array Methods

### Preferred Methods
```javascript
// ✅ Use appropriate array methods
const doubled = numbers.map(n => n * 2);
const filtered = items.filter(item => item.active);
const found = users.find(user => user.id === targetId);
const hasAdmin = users.some(user => user.role === 'admin');
const allValid = items.every(item => item.isValid);
const total = prices.reduce((sum, price) => sum + price, 0);

// ❌ Avoid for loops when array methods work
const doubled = [];
for (let i = 0; i < numbers.length; i++) {
  doubled.push(numbers[i] * 2);  // Use map instead
}
```

## Object Patterns

### Object Shorthand
```javascript
// ✅ Use property shorthand
const name = 'John';
const age = 30;
const user = { name, age };

// ✅ Use method shorthand
const obj = {
  method() {
    return 'result';
  }
};

// ❌ Avoid redundant syntax
const user = { name: name, age: age };  // Use shorthand
const obj = {
  method: function() {  // Use method shorthand
    return 'result';
  }
};
```

### Optional Chaining
```javascript
// ✅ Use optional chaining
const city = user?.address?.city;
const result = obj.method?.();
const item = array?.[index];

// ❌ Avoid verbose checking
const city = user && user.address && user.address.city;  // Use ?.
```

### Nullish Coalescing
```javascript
// ✅ Use ?? for null/undefined checks
const port = config.port ?? 3000;
const name = user.name ?? 'Anonymous';

// ❌ Be careful with || 
const count = input.count || 10;  // Problem if count is 0
const count = input.count ?? 10;  // Correct for 0 values
```

## Module System

### Imports and Exports
```javascript
// ✅ Named exports for utilities
export function formatDate(date) { }
export function parseUrl(url) { }
export const CONFIG = { };

// ✅ Default export for main component/class
export default class UserService { }

// ✅ Import patterns
import UserService from './UserService';
import { formatDate, parseUrl } from './utils';
import * as utils from './utils';

// ❌ Avoid mixing module systems
const module = require('./module');  // Use ES6 imports
module.exports = { };  // Use ES6 exports
```

## Error Handling

### Try-Catch Patterns
```javascript
// ✅ Specific error handling
try {
  const data = await riskyOperation();
  return processData(data);
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Validation failed:', error.message);
    return defaultValue;
  }
  throw error;  // Re-throw unexpected errors
}

// ✅ Error context
class CustomError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
    this.name = 'CustomError';
  }
}
```

## Comments

### Comment Style
```javascript
// ✅ Single-line comments for brief notes
const result = calculate();  // Cache result for performance

// ✅ Multi-line comments for documentation
/**
 * Calculates the total price including tax.
 * @param {number} price - Base price
 * @param {number} taxRate - Tax rate as decimal
 * @returns {number} Total price with tax
 */
function calculateTotal(price, taxRate) {
  return price * (1 + taxRate);
}

// ✅ TODO comments with context
// TODO(john): Optimize this for large datasets
// FIXME: Handle edge case when array is empty
```

## Rationale

### Why These Conventions

1. **Modern Syntax**: ES6+ features are cleaner and safer
2. **Const by Default**: Prevents accidental reassignment
3. **Arrow Functions**: Cleaner syntax for simple functions
4. **Destructuring**: Reduces repetition and improves clarity
5. **Async/Await**: More readable than promise chains

### Benefits
- **Readability**: Modern syntax is cleaner
- **Safety**: Const and proper scoping prevent bugs
- **Performance**: Modern features often optimize better
- **Maintainability**: Consistent patterns ease updates
- **Developer Experience**: Better IDE support and tooling