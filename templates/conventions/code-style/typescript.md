---
id: code-style-typescript
type: convention
category: code-style
title: TypeScript Specific Conventions
applies_to: code
enforcement: required
dependencies:
  - code-style/javascript
  - code-style/general
version: 1.0.0
status: stable
---

# TypeScript Code Style Conventions

## Convention
TypeScript code must leverage type safety while maintaining readability and following consistent patterns.

## Type Annotations

### Basic Types
```typescript
// ✅ Explicit types when not inferrable
const userName: string = getUserName();
const count: number = 0;
const isActive: boolean = true;
const items: string[] = [];

// ✅ Let TypeScript infer when obvious
const message = 'Hello';  // Clearly a string
const total = 100;  // Clearly a number
const users = ['John', 'Jane'];  // Clearly string[]

// ❌ Avoid unnecessary annotations
const name: string = 'John';  // Type is obvious
```

### Interface vs Type
```typescript
// ✅ Use interface for objects and classes
interface User {
  id: string;
  name: string;
  email: string;
}

interface UserService {
  getUser(id: string): Promise<User>;
  updateUser(user: User): Promise<void>;
}

// ✅ Use type for unions, intersections, and aliases
type Status = 'pending' | 'active' | 'inactive';
type ID = string | number;
type UserWithRole = User & { role: string };
type Callback = (data: any) => void;

// ✅ Extend interfaces
interface AdminUser extends User {
  permissions: string[];
}
```

## Component Props

### React Component Types
```typescript
// ✅ Interface for component props
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}

// ✅ With HTML attributes
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  isLoading?: boolean;
}

// ✅ ForwardRef components
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', ...props }, ref) => {
    return <button ref={ref} className={className} {...props} />;
  }
);
Button.displayName = 'Button';
```

## Generics

### Generic Functions
```typescript
// ✅ Use generics for reusable functions
function identity<T>(value: T): T {
  return value;
}

function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// ✅ Generic constraints
function processArray<T extends { id: string }>(items: T[]): T[] {
  return items.filter(item => item.id !== '');
}

// ✅ Multiple type parameters
function map<T, U>(array: T[], fn: (item: T) => U): U[] {
  return array.map(fn);
}
```

### Generic Interfaces
```typescript
// ✅ Generic interfaces
interface ApiResponse<T> {
  data: T;
  error: string | null;
  status: number;
}

interface Repository<T> {
  find(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<T>;
  delete(id: string): Promise<void>;
}
```

## Type Guards

### Custom Type Guards
```typescript
// ✅ Type predicate functions
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isUser(obj: any): obj is User {
  return obj && typeof obj.id === 'string' && typeof obj.name === 'string';
}

// ✅ Using type guards
function processValue(value: string | number) {
  if (typeof value === 'string') {
    return value.toUpperCase();  // TypeScript knows it's string
  }
  return value * 2;  // TypeScript knows it's number
}
```

## Utility Types

### Common Utility Types
```typescript
// ✅ Partial - all properties optional
type PartialUser = Partial<User>;

// ✅ Required - all properties required
type RequiredUser = Required<User>;

// ✅ Readonly - all properties readonly
type ReadonlyUser = Readonly<User>;

// ✅ Pick - select properties
type UserPreview = Pick<User, 'id' | 'name'>;

// ✅ Omit - exclude properties
type UserWithoutEmail = Omit<User, 'email'>;

// ✅ Record - object with specific keys
type UserMap = Record<string, User>;

// ✅ Extract and Exclude
type ActiveStatus = Extract<Status, 'active' | 'pending'>;
type InactiveStatus = Exclude<Status, 'active'>;
```

## Enums vs Const Assertions

### When to Use Each
```typescript
// ✅ Const assertion for simple constants
const Colors = {
  RED: '#ff0000',
  GREEN: '#00ff00',
  BLUE: '#0000ff'
} as const;

type Color = typeof Colors[keyof typeof Colors];

// ✅ String literal unions preferred over enums
type Theme = 'light' | 'dark' | 'auto';

// ⚠️ Use enum sparingly (when needed for JavaScript)
enum HttpStatus {
  OK = 200,
  NotFound = 404,
  ServerError = 500
}
```

## Async Types

### Promise Types
```typescript
// ✅ Explicit Promise types
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}

// ✅ Async function types
type AsyncFunction<T> = () => Promise<T>;
type AsyncCallback<T> = (data: T) => Promise<void>;

// ✅ Error handling types
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

async function safeRequest<T>(url: string): Promise<Result<T>> {
  try {
    const data = await fetch(url).then(r => r.json());
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}
```

## Strict Mode Settings

### Recommended tsconfig
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

## Type Assertions

### When to Use
```typescript
// ✅ When you know more than TypeScript
const canvas = document.getElementById('canvas') as HTMLCanvasElement;
const data = JSON.parse(jsonString) as UserData;

// ⚠️ Avoid type assertions when possible
const user = {} as User;  // Dangerous - prefer proper initialization

// ✅ Non-null assertion when certain
const element = document.querySelector('.my-element')!;  // When you're sure it exists
```

## Naming Conventions

### Type and Interface Names
```typescript
// ✅ PascalCase for types and interfaces
interface UserProfile { }
type ApiResponse = { };

// ✅ Suffix for specific types
interface ButtonProps { }  // Component props
interface UserData { }     // Data structures
type UserMap = { };        // Collections
type UserId = string;      // Aliases

// ❌ Avoid Hungarian notation
interface IUser { }        // Don't prefix with I
type TResponse = { };      // Don't prefix with T
```

## Examples

### ✅ Good TypeScript
```typescript
interface TodoItem {
  id: string;
  title: string;
  completed: boolean;
  createdAt: Date;
}

interface TodoStore {
  items: TodoItem[];
  addItem(title: string): void;
  toggleItem(id: string): void;
  removeItem(id: string): void;
}

class TodoService implements TodoStore {
  constructor(private items: TodoItem[] = []) {}
  
  addItem(title: string): void {
    const item: TodoItem = {
      id: crypto.randomUUID(),
      title,
      completed: false,
      createdAt: new Date()
    };
    this.items.push(item);
  }
  
  toggleItem(id: string): void {
    const item = this.items.find(i => i.id === id);
    if (item) {
      item.completed = !item.completed;
    }
  }
  
  removeItem(id: string): void {
    this.items = this.items.filter(i => i.id !== id);
  }
}
```

## Rationale

### Why These Conventions

1. **Type Safety**: Catch errors at compile time
2. **Documentation**: Types serve as inline documentation
3. **Refactoring**: Types make refactoring safer
4. **IntelliSense**: Better IDE support and autocomplete
5. **Consistency**: Team follows same patterns

### Benefits
- **Fewer Bugs**: Type checking catches errors early
- **Better DX**: Autocomplete and inline docs
- **Maintainability**: Types make code self-documenting
- **Confidence**: Refactor without fear
- **Team Velocity**: Less time debugging runtime errors