---
id: naming-functions
type: convention
category: naming
title: Function Naming Patterns
applies_to: code
enforcement: required
dependencies:
  - naming-variables
version: 1.0.0
status: stable
---

# Function Naming Patterns

## Convention
Functions must use descriptive verb-based names in camelCase that clearly indicate their purpose and behavior.

## Function Type Conventions

### Regular Functions
- **Pattern**: `verbNoun` in camelCase
- **Examples**: `getUserData`, `formatDate`, `validateEmail`
- **Rule**: Start with action verb

### Event Handlers
- **Pattern**: `handle` + `EventName`
- **Examples**: `handleClick`, `handleSubmit`, `handleInputChange`
- **Usage**: DOM events and user interactions

### Boolean Functions
- **Pattern**: `is/has/should/can` + `State`
- **Examples**: `isValid`, `hasPermission`, `shouldUpdate`, `canEdit`
- **Returns**: Always boolean

### Async Functions
- **Pattern**: `fetch/load/get/save` + `Resource`
- **Examples**: `fetchUserData`, `loadConfig`, `saveProfile`
- **Indicator**: Action implies async operation

### React Hooks
- **Pattern**: `use` + `PascalCase`
- **Examples**: `useAuth`, `useLocalStorage`, `useMediaQuery`
- **Rule**: Must start with 'use' (lowercase)

### Utility Functions
- **Pattern**: `actionObject` or `objectAction`
- **Examples**: `parseJson`, `formatCurrency`, `debounce`
- **Purpose**: Pure functions with clear input/output

## Examples

### Good Examples
```typescript
// Regular functions
function getUserData(userId: string) { }
function calculateTotal(items: Item[]) { }
function sendNotification(message: string) { }

// Event handlers
const handleClick = (event: MouseEvent) => { };
const handleFormSubmit = (data: FormData) => { };
const handleInputChange = (value: string) => { };

// Boolean functions
function isValidEmail(email: string): boolean { }
function hasAdminRole(user: User): boolean { }
function canEditPost(post: Post, user: User): boolean { }

// Async functions
async function fetchUserProfile(id: string) { }
async function saveUserSettings(settings: Settings) { }
async function loadApplicationData() { }

// React hooks
function useLocalStorage(key: string) { }
function useDebounce(value: string, delay: number) { }
function useAuth() { }

// Utility functions
function formatDate(date: Date): string { }
function parseQueryString(query: string): object { }
function debounce(fn: Function, delay: number) { }
```

## Anti-patterns

### Wrong Patterns
```typescript
// Wrong casing
function GetUserData() { }         ❌ Should be camelCase
function get_user_data() { }       ❌ No underscores
function VALIDATE_EMAIL() { }      ❌ Not a constant

// Non-descriptive names
function process(data) { }         ❌ Too vague
function doStuff() { }             ❌ Unclear purpose
function handler() { }             ❌ What does it handle?

// Missing verb
function userData() { }            ❌ Should be getUserData
function validation() { }          ❌ Should be validate

// Wrong boolean naming
function valid(email) { }          ❌ Should be isValid
function permission() { }          ❌ Should be hasPermission

// Wrong hook naming
function UseAuth() { }             ❌ 'use' should be lowercase
function authHook() { }            ❌ Must start with 'use'
function useauth() { }             ❌ Should be useAuth

// Misleading async names
function getUserData() {           ❌ Async should be clear
  return fetch('/api/user');       ❌ Use fetchUserData
}
```

## Method Naming in Classes

### Public Methods
- Follow same rules as functions
- **Examples**: `getUserName()`, `calculateTotal()`

### Private Methods
- **Pattern**: Prefix with underscore (legacy) or use # (modern)
- **Examples**: `_validateInput()`, `#processData()`

### Getters/Setters
- **Pattern**: `get/set` + `PropertyName`
- **Examples**: `getName()`, `setName()`, `get name()`, `set name()`

```typescript
class User {
  // Public methods
  getUserData() { }
  updateProfile() { }
  
  // Private methods (modern)
  #validateData() { }
  #sanitizeInput() { }
  
  // Getters/Setters
  get fullName() { }
  set fullName(value) { }
}
```

## Special Naming Patterns

### Factory Functions
- **Pattern**: `create` + `ObjectType`
- **Examples**: `createUser`, `createButton`, `createStore`

### Converter Functions
- **Pattern**: `xToY` format
- **Examples**: `jsonToXml`, `celsiusToFahrenheit`, `arrayToObject`

### Validator Functions
- **Pattern**: `validate` + `Target`
- **Examples**: `validateEmail`, `validateForm`, `validatePassword`

### Builder Functions
- **Pattern**: `build` + `Target`
- **Examples**: `buildQuery`, `buildUrl`, `buildConfiguration`

## Rationale

### Why These Conventions

1. **Verb-First**: Immediately indicates action/behavior
2. **camelCase**: JavaScript standard for functions
3. **Descriptive Names**: Self-documenting code
4. **Pattern Consistency**: Predictable naming aids discovery
5. **Type Indicators**: Name hints at return type/behavior

### Benefits
- **Clarity**: Purpose clear from name alone
- **Searchability**: Easy to find related functions
- **Maintainability**: Clear intent reduces bugs
- **Onboarding**: New developers understand quickly
- **IDE Support**: Better autocomplete and suggestions