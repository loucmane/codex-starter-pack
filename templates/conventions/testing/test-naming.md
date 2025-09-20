---
id: test-naming
type: convention
category: testing
title: Test File and Function Naming
applies_to: code
enforcement: required
dependencies:
  - test-structure
version: 1.0.0
status: stable
---

# Test Naming Conventions

## Convention
Test files and test cases must follow clear naming patterns that describe what is being tested and expected behavior.

## Test File Naming

### Unit Test Files
- **Pattern**: `[filename].test.[ext]` or `[filename].spec.[ext]`
- **Location**: Colocated with source file
- **Examples**:
  - `Button.test.tsx` for `Button.tsx`
  - `formatDate.test.ts` for `formatDate.ts`
  - `auth.service.spec.ts` for `auth.service.ts`

### Integration Test Files
- **Pattern**: `[feature].integration.test.[ext]`
- **Location**: `tests/integration/` or `__tests__/integration/`
- **Examples**:
  - `user-auth.integration.test.ts`
  - `api-workflow.integration.test.ts`

### E2E Test Files
- **Pattern**: `[feature].e2e.test.[ext]` or `[feature].e2e-spec.[ext]`
- **Location**: `tests/e2e/` or `e2e/`
- **Examples**:
  - `checkout-flow.e2e.test.ts`
  - `user-journey.e2e-spec.ts`

## Test Suite Naming

### Describe Blocks
```javascript
// ✅ Component/Class/Module name
describe('Button', () => {
  describe('when clicked', () => {
    // Nested context
  });
});

describe('formatDate', () => {
  describe('with valid date', () => {
    // Test cases
  });
});

describe('UserService', () => {
  describe('getUser', () => {
    // Method-specific tests
  });
});
```

## Test Case Naming

### It/Test Statements
```javascript
// ✅ Good patterns
it('should return formatted date string', () => {});
it('should throw error when date is invalid', () => {});
it('should handle null input gracefully', () => {});
it('renders with default props', () => {});
it('calls onClick handler when clicked', () => {});

// ❌ Bad patterns
it('works', () => {});  // Too vague
it('test 1', () => {});  // Not descriptive
it('error', () => {});  // Unclear what error
```

### Test Naming Patterns

#### Behavior-Driven
```javascript
// Pattern: should [expected behavior] when [condition]
it('should return true when user is admin', () => {});
it('should throw ValidationError when email is invalid', () => {});
it('should update state when props change', () => {});
```

#### Given-When-Then
```javascript
// Pattern: given [context], when [action], then [result]
it('given empty array, when push is called, then length is 1', () => {});
it('given logged out user, when accessing protected route, then redirects to login', () => {});
```

#### Present Tense
```javascript
// Pattern: [verb] [expected outcome]
it('returns the sum of two numbers', () => {});
it('throws error for negative input', () => {});
it('renders loading spinner during fetch', () => {});
```

## Examples

### ✅ Good Test Names
```javascript
// Unit test for utility function
describe('formatCurrency', () => {
  it('should format positive numbers with dollar sign', () => {
    expect(formatCurrency(10)).toBe('$10.00');
  });
  
  it('should handle negative numbers with parentheses', () => {
    expect(formatCurrency(-10)).toBe('($10.00)');
  });
  
  it('should round to two decimal places', () => {
    expect(formatCurrency(10.999)).toBe('$11.00');
  });
});

// Component test
describe('LoginForm', () => {
  describe('validation', () => {
    it('should show error when email is empty', () => {});
    it('should show error when password is less than 8 characters', () => {});
    it('should enable submit button when form is valid', () => {});
  });
  
  describe('submission', () => {
    it('should call onSubmit with form data when submitted', () => {});
    it('should disable form during submission', () => {});
    it('should show error message on failed submission', () => {});
  });
});
```

### ❌ Poor Test Names
```javascript
// Too vague
describe('utils', () => {
  it('works correctly', () => {});
  it('handles errors', () => {});
  it('test case 1', () => {});
});

// No clear structure
describe('Thing', () => {
  it('does stuff', () => {});
  it('more stuff', () => {});
  it('fails sometimes', () => {});
});
```

## Test Organization

### Grouping Related Tests
```javascript
describe('UserService', () => {
  describe('authentication', () => {
    describe('login', () => {
      it('should return token for valid credentials', () => {});
      it('should throw error for invalid credentials', () => {});
    });
    
    describe('logout', () => {
      it('should clear user session', () => {});
      it('should revoke token', () => {});
    });
  });
  
  describe('profile management', () => {
    describe('updateProfile', () => {
      it('should update user data', () => {});
      it('should validate required fields', () => {});
    });
  });
});
```

## Special Test Types

### Snapshot Tests
```javascript
it('should match snapshot', () => {});
it('should match snapshot with props', () => {});
it('should match snapshot after interaction', () => {});
```

### Performance Tests
```javascript
it('should render list of 1000 items in under 100ms', () => {});
it('should complete calculation in under 10ms', () => {});
```

### Accessibility Tests
```javascript
it('should have no accessibility violations', () => {});
it('should be keyboard navigable', () => {});
it('should have proper ARIA labels', () => {});
```

## Test File Structure

### Standard Structure
```javascript
// Imports
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

// Test suite
describe('Button', () => {
  // Setup/teardown if needed
  beforeEach(() => {
    // Setup
  });
  
  afterEach(() => {
    // Cleanup
  });
  
  // Group related tests
  describe('rendering', () => {
    it('should render with text', () => {});
    it('should apply className', () => {});
  });
  
  describe('interactions', () => {
    it('should call onClick when clicked', () => {});
    it('should be disabled when disabled prop is true', () => {});
  });
});
```

## Rationale

### Why These Conventions

1. **Clarity**: Descriptive names explain test purpose
2. **Searchability**: Consistent patterns aid finding tests
3. **Documentation**: Test names document behavior
4. **Debugging**: Clear names speed up failure diagnosis
5. **Maintenance**: Organized tests easier to update

### Benefits
- **Self-Documenting**: Tests serve as behavior documentation
- **Quick Understanding**: Clear what's being tested
- **Better Coverage**: Organized tests reveal gaps
- **Easier Debugging**: Know what broke from test name
- **Team Alignment**: Everyone writes similar tests