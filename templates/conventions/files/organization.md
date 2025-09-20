---
id: file-organization
type: convention
category: files
title: General File Organization Principles
applies_to: all
enforcement: required
dependencies:
  - directory-structure
  - special-files
version: 1.0.0
status: stable
---

# General File Organization Principles

## Convention
Files must be organized in a logical, consistent structure that promotes discoverability, maintainability, and scalability.

## Core Principles

### 1. Colocation
- **Principle**: Keep related files together
- **Implementation**: Components with their tests, styles, and utilities
- **Benefits**: Easier navigation, clearer relationships

### 2. Single Responsibility
- **Principle**: One file, one purpose
- **Implementation**: Separate concerns into distinct files
- **Benefits**: Better testability, reusability

### 3. Predictable Structure
- **Principle**: Consistent patterns across the codebase
- **Implementation**: Same structure in all packages/modules
- **Benefits**: Reduced cognitive load, faster onboarding

## File Organization Patterns

### Component Organization
```
components/
  Button/
    Button.tsx           # Component implementation
    Button.test.tsx      # Component tests
    Button.stories.tsx   # Storybook stories
    Button.module.css    # Component styles
    index.ts            # Public exports
    types.ts            # Type definitions
    utils.ts            # Helper functions
```

### Feature Organization
```
features/
  authentication/
    components/         # Feature-specific components
    hooks/             # Feature-specific hooks
    services/          # API calls and business logic
    store/             # State management
    types/             # Type definitions
    utils/             # Helper functions
    index.ts           # Public API
```

### Package Organization (Monorepo)
```
packages/
  web/                 # Web application
    src/
      components/
      pages/
      hooks/
      utils/
  ui/                  # Shared UI library
    src/
      components/
      themes/
      tokens/
  shared/              # Shared utilities
    src/
      types/
      utils/
      constants/
```

## Import Order Convention

### Standard Import Order
```typescript
// 1. React imports
import React, { useState, useEffect } from 'react'

// 2. External library imports
import { motion } from 'framer-motion'
import clsx from 'clsx'

// 3. Monorepo package imports
import { Button } from '@repo/ui'
import type { Animal } from '@repo/shared'

// 4. Local imports
import { Header } from '@/components/Header'
import { useTheme } from '@/hooks/useTheme'

// 5. Type imports
import type { ButtonProps } from './types'

// 6. Style imports
import styles from './Button.module.css'
```

## Examples

### Good Organization
```
✅ Clear separation of concerns
src/
  components/           # Presentational components
  containers/          # Container components
  hooks/               # Custom hooks
  services/            # API and external services
  store/               # State management
  utils/               # Utility functions
  types/               # Shared type definitions
  constants/           # App constants

✅ Colocated related files
components/Button/
  Button.tsx
  Button.test.tsx
  Button.stories.tsx
  index.ts
```

## Anti-patterns

### Poor Organization
```
❌ Mixed concerns
src/
  Button.tsx           # Component in root
  api.js              # API calls in root
  utils.ts            # Utils in root
  LoginForm.tsx       # Another component in root
  styles.css          # Global styles in root

❌ Scattered related files
components/Button.tsx
tests/Button.test.tsx     # Test far from component
styles/button.css         # Style far from component
types/button.types.ts     # Types far from component

❌ Deep nesting
src/components/ui/buttons/primary/default/Button.tsx  # Too deep
```

## File Size Guidelines

### Recommended Limits
- **Components**: < 300 lines
- **Utilities**: < 100 lines per function
- **Test files**: Mirror source file structure
- **Config files**: < 200 lines

### When to Split
- File exceeds 300 lines
- Multiple responsibilities evident
- Reusable logic identified
- Complex logic needs isolation

## Index Files

### Purpose
- Control public API
- Simplify imports
- Hide implementation details

### Pattern
```typescript
// components/Button/index.ts
export { Button } from './Button'
export type { ButtonProps } from './types'

// Usage
import { Button } from '@/components/Button' // Clean import
```

## Rationale

### Why These Conventions

1. **Colocation**: Related files together reduces navigation
2. **Predictability**: Consistent structure aids discovery
3. **Scalability**: Patterns that work at any size
4. **Maintainability**: Clear organization reduces complexity
5. **Team Efficiency**: Everyone knows where things go

### Benefits
- **Faster Development**: Less time searching for files
- **Easier Refactoring**: Clear boundaries and dependencies
- **Better Testing**: Tests next to source code
- **Cleaner Imports**: Logical import paths
- **Reduced Conflicts**: Clear ownership boundaries