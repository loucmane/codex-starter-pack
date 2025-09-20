---
id: naming-variables
type: convention
category: naming
title: Variable Naming Conventions
applies_to: code
enforcement: required
dependencies:
  - naming-functions
version: 1.0.0
status: stable
---

# Variable Naming Conventions

## Convention
Variables must use descriptive names following consistent casing patterns based on their type and scope.

## Variable Type Conventions

### Regular Variables
- **Pattern**: `camelCase`
- **Examples**: `userName`, `isLoading`, `currentIndex`
- **Scope**: Function and block scope

### Constants
- **Pattern**: `UPPER_SNAKE_CASE`
- **Examples**: `MAX_RETRIES`, `API_URL`, `DEFAULT_TIMEOUT`
- **Scope**: Module or global constants

### Boolean Variables
- **Pattern**: `is/has/should/can` prefix + `PascalCase`
- **Examples**: `isLoading`, `hasError`, `shouldUpdate`, `canEdit`
- **Purpose**: Clearly indicates boolean type

### Private Variables
- **Pattern**: `_camelCase` (underscore prefix)
- **Examples**: `_internalState`, `_privateMethod`
- **Note**: Avoid in modern JS/TS, use # for private fields

### Component Props
- **Pattern**: `camelCase`
- **Examples**: `onClick`, `className`, `variant`
- **Interfaces**: `ComponentNameProps`

### React State
- **Pattern**: `[value, setValue]` for useState
- **Examples**: `[user, setUser]`, `[count, setCount]`
- **Consistency**: Always use set prefix for setters

## Examples

### Good Examples
```typescript
// Regular variables
const userName = 'John';
const itemCount = 42;
const selectedItems = [];

// Constants
const MAX_RETRIES = 3;
const API_BASE_URL = 'https://api.example.com';
const DEFAULT_PAGE_SIZE = 20;

// Booleans
const isLoading = true;
const hasPermission = false;
const shouldRetry = true;
const canDelete = user.role === 'admin';

// React state
const [user, setUser] = useState(null);
const [isModalOpen, setIsModalOpen] = useState(false);

// Component props
interface ButtonProps {
  variant: 'primary' | 'secondary';
  isDisabled: boolean;
  onClick: () => void;
}
```

## Anti-patterns

### Wrong Patterns
```typescript
// Wrong casing
const UserName = 'John';          ❌ Should be camelCase
const user_name = 'John';          ❌ No underscores
const USERNAME = 'John';           ❌ Not a constant

// Non-descriptive names
const d = new Date();              ❌ Too short
const temp = userData;             ❌ Unclear purpose
const data = fetchResults();       ❌ Too generic

// Wrong boolean naming
const loading = true;              ❌ Should be isLoading
const error = false;               ❌ Should be hasError
const update = true;               ❌ Should be shouldUpdate

// Wrong constant naming
const maxRetries = 3;              ❌ Should be UPPER_SNAKE
const apiUrl = 'http://...';       ❌ Should be API_URL

// Inconsistent state naming
const [user, updateUser] = useState();  ❌ Should be setUser
const [open, toggleOpen] = useState();  ❌ Should be setOpen
```

## Special Cases

### Loop Variables
- **Simple loops**: `i`, `j`, `k` are acceptable
- **Array methods**: Use descriptive names
```typescript
// Acceptable
for (let i = 0; i < items.length; i++) { }

// Better for array methods
items.map(item => item.name)           ✅
items.map(i => i.name)                 ❌ Too vague
```

### Destructuring
- Keep original names when clear
- Rename for clarity when needed
```typescript
const { name, email } = user;                    ✅ Clear
const { n, e } = user;                          ❌ Too short
const { name: userName, email: userEmail } = user;  ✅ When needed
```

### Event Handlers
- **Pattern**: `handle` + `EventName`
- **Examples**: `handleClick`, `handleSubmit`, `handleChange`
```typescript
const handleClick = (event) => { };
const handleFormSubmit = (data) => { };
```

## Rationale

### Why These Conventions

1. **camelCase**: JavaScript standard for variables
2. **UPPER_SNAKE**: Universally recognized as constants
3. **Boolean Prefixes**: Self-documenting boolean intent
4. **Descriptive Names**: Code is read more than written
5. **Consistent Patterns**: Reduces mental overhead

### Benefits
- **Self-documenting**: Names explain purpose
- **Type Hints**: Naming patterns indicate type
- **Searchability**: Consistent names easier to find
- **Maintainability**: Clear intent reduces bugs
- **Team Alignment**: Everyone uses same patterns