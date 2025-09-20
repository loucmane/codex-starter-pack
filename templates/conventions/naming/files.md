---
id: naming-files
type: convention
category: naming
title: File Naming Standards
applies_to: files
enforcement: required
dependencies:
  - naming-variables
  - naming-functions
version: 1.0.0
status: stable
---

# File Naming Standards

## Convention
Files must follow specific naming patterns based on their type and purpose to ensure consistency and discoverability across the codebase.

## File Type Conventions

### React Components
- **Pattern**: `PascalCase.tsx`
- **Examples**: `Button.tsx`, `HeaderNav.tsx`, `UserProfile.tsx`
- **Location**: `components/` directories

### Utility Files
- **Pattern**: `camelCase.ts`
- **Examples**: `formatDate.ts`, `parseUrl.ts`, `validateEmail.ts`
- **Location**: `utils/` or `lib/` directories

### Hooks
- **Pattern**: `use[PascalCase].ts`
- **Examples**: `useLocalStorage.ts`, `useMediaQuery.ts`, `useAuth.ts`
- **Location**: `hooks/` directories

### Type Definition Files
- **Pattern**: `camelCase.types.ts`
- **Examples**: `animal.types.ts`, `navigation.types.ts`, `user.types.ts`
- **Location**: `types/` directories

### Test Files
- **Pattern**: `[originalName].test.ts` or `[originalName].spec.ts`
- **Examples**: `Button.test.tsx`, `formatDate.test.ts`, `auth.spec.ts`
- **Location**: Colocated with source file

### Style Files
- **Pattern**: `kebab-case.css` or `kebab-case.scss`
- **Examples**: `button-styles.css`, `header-nav.scss`, `global-styles.css`
- **Location**: Colocated or in `styles/` directory

### Configuration Files
- **Pattern**: `kebab-case.config.js` or dot files
- **Examples**: `webpack.config.js`, `.eslintrc.js`, `jest.config.js`
- **Location**: Project root or config directory

## Special Files

### Session Documentation
- **Pattern**: `sessions/`
- **Purpose**: Track AI development sessions
- **Location**: Project root

### Work Tracking
- **Pattern**: `TRACKER.md`, `HANDOFF.md`, `FINDINGS.md`
- **Purpose**: Document work progress and handoffs
- **Location**: Work tracking folders

### Memory Files
- **Pattern**: `session_YYYY-MM-DD_description.md`
- **Examples**: `session_2025-07-09_template_system.md`
- **Location**: `.serena/memories/`

## Examples

### Good Examples
```bash
# Components
components/Button.tsx           ✅ PascalCase for React
components/UserProfile.tsx      ✅ Clear component name

# Utilities
utils/formatDate.ts             ✅ camelCase for utilities
utils/parseJson.ts              ✅ Descriptive function name

# Hooks
hooks/useLocalStorage.ts        ✅ use prefix for hooks
hooks/useAuth.ts                ✅ Clear hook purpose

# Tests
Button.test.tsx                 ✅ Colocated test file
formatDate.test.ts              ✅ Matches source name
```

## Anti-patterns

### Wrong Patterns
```bash
# Wrong component naming
components/button.tsx           ❌ Should be PascalCase
components/user-profile.tsx     ❌ Should be UserProfile.tsx

# Wrong utility naming
utils/FormatDate.ts             ❌ Should be camelCase
utils/format_date.ts            ❌ No underscores

# Wrong hook naming
hooks/localStorage.ts           ❌ Missing 'use' prefix
hooks/UseAuth.ts                ❌ 'use' should be lowercase

# Wrong test naming
button-tests.tsx                ❌ Should be Button.test.tsx
test-format-date.ts             ❌ Should be formatDate.test.ts
```

## Rationale

### Why These Conventions

1. **PascalCase for Components**: React convention, immediately identifies components
2. **camelCase for Utilities**: JavaScript standard for functions/modules
3. **use Prefix for Hooks**: React convention, enables linter rules
4. **Colocated Tests**: Easier to find and maintain tests
5. **kebab-case for CSS**: CSS/SCSS standard convention
6. **Consistent Patterns**: Reduces cognitive load, improves discoverability

### Benefits
- **Discoverability**: Predictable names make files easier to find
- **Clarity**: File name indicates content type
- **Tool Support**: IDEs and linters can enforce patterns
- **Team Consistency**: Everyone follows same rules
- **Import Clarity**: Clear what you're importing from filename