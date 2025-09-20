---
id: test-structure
type: convention
category: testing
title: Test Organization and Structure
applies_to: code
enforcement: required
dependencies:
  - test-naming
version: 1.0.0
status: stable
---

# Test Structure Conventions

## Convention
Tests must be organized in a clear, maintainable structure that promotes comprehensive coverage and easy maintenance.

## Test Directory Structure

### Standard Layout
```
project/
├── src/
│   ├── components/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx      # Colocated unit test
│   │   │   └── Button.stories.tsx   # Storybook stories
│   ├── utils/
│   │   ├── formatDate.ts
│   │   └── formatDate.test.ts       # Colocated unit test
├── tests/                             # Separate test directory
│   ├── integration/                  # Integration tests
│   ├── e2e/                          # End-to-end tests
│   ├── fixtures/                     # Test data
│   ├── mocks/                        # Mock implementations
│   └── setup/                        # Test configuration
```

## Test File Organization

### Import Order
```javascript
// 1. Testing library imports
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// 2. Mock imports
import { vi } from 'vitest';

// 3. Component/module under test
import { Button } from './Button';

// 4. Dependencies and helpers
import { theme } from '@/theme';
import { createMockUser } from '@/tests/fixtures/user';

// 5. Type imports
import type { ButtonProps } from './Button.types';
```

### Test Structure Pattern
```javascript
describe('ComponentName', () => {
  // Setup variables
  let mockFn: jest.Mock;
  let container: HTMLElement;
  
  // Setup and teardown
  beforeEach(() => {
    mockFn = vi.fn();
    // Common setup
  });
  
  afterEach(() => {
    vi.clearAllMocks();
    // Cleanup
  });
  
  // Group by functionality
  describe('rendering', () => {
    it('should render with default props', () => {});
    it('should render with custom className', () => {});
  });
  
  describe('props', () => {
    it('should handle variant prop', () => {});
    it('should handle disabled state', () => {});
  });
  
  describe('interactions', () => {
    it('should call onClick when clicked', () => {});
    it('should prevent click when disabled', () => {});
  });
  
  describe('edge cases', () => {
    it('should handle null children', () => {});
    it('should handle very long text', () => {});
  });
});
```

## Test Patterns

### Arrange-Act-Assert (AAA)
```javascript
it('should calculate total with tax', () => {
  // Arrange
  const price = 100;
  const taxRate = 0.1;
  
  // Act
  const total = calculateTotal(price, taxRate);
  
  // Assert
  expect(total).toBe(110);
});
```

### Given-When-Then
```javascript
it('should redirect to login when unauthorized', () => {
  // Given - user is not authenticated
  const user = null;
  
  // When - accessing protected route
  const result = requireAuth(user, '/dashboard');
  
  // Then - redirects to login
  expect(result.redirect).toBe('/login');
  expect(result.returnUrl).toBe('/dashboard');
});
```

## Component Testing Structure

### Basic Component Test
```javascript
describe('Button', () => {
  const defaultProps: ButtonProps = {
    onClick: vi.fn(),
    children: 'Click me'
  };
  
  const renderButton = (props: Partial<ButtonProps> = {}) => {
    return render(<Button {...defaultProps} {...props} />);
  };
  
  it('should render children', () => {
    renderButton();
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('should handle click events', () => {
    const handleClick = vi.fn();
    renderButton({ onClick: handleClick });
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Testing Hooks
```javascript
describe('useCounter', () => {
  it('should increment counter', () => {
    const { result } = renderHook(() => useCounter());
    
    expect(result.current.count).toBe(0);
    
    act(() => {
      result.current.increment();
    });
    
    expect(result.current.count).toBe(1);
  });
});
```

## Mock Organization

### Mock Files
```javascript
// tests/mocks/api.ts
export const mockApi = {
  getUser: vi.fn().mockResolvedValue({ id: '1', name: 'John' }),
  updateUser: vi.fn().mockResolvedValue({ success: true })
};

// Usage in tests
import { mockApi } from '@/tests/mocks/api';

vi.mock('@/services/api', () => ({
  api: mockApi
}));
```

### Mock Data Fixtures
```javascript
// tests/fixtures/user.ts
export const createMockUser = (overrides = {}) => ({
  id: '123',
  name: 'Test User',
  email: 'test@example.com',
  role: 'user',
  ...overrides
});

// Usage
const adminUser = createMockUser({ role: 'admin' });
```

## Test Categories

### Unit Tests
```javascript
// Focus: Single unit in isolation
describe('formatDate (unit)', () => {
  it('should format ISO date to readable format', () => {
    const date = '2025-01-01T00:00:00Z';
    expect(formatDate(date)).toBe('January 1, 2025');
  });
});
```

### Integration Tests
```javascript
// Focus: Multiple units working together
describe('UserProfile (integration)', () => {
  it('should fetch and display user data', async () => {
    render(<UserProfile userId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests
```javascript
// Focus: Complete user workflows
describe('Checkout Flow (e2e)', () => {
  it('should complete purchase from cart to confirmation', async () => {
    await page.goto('/cart');
    await page.click('[data-testid="checkout-button"]');
    await page.fill('[name="email"]', 'test@example.com');
    await page.click('[data-testid="submit-order"]');
    await expect(page).toHaveURL('/confirmation');
  });
});
```

## Test Data Management

### Test Data Builders
```javascript
class UserBuilder {
  private user = {
    id: '1',
    name: 'Default User',
    email: 'user@example.com'
  };
  
  withName(name: string) {
    this.user.name = name;
    return this;
  }
  
  withEmail(email: string) {
    this.user.email = email;
    return this;
  }
  
  build() {
    return { ...this.user };
  }
}

// Usage
const user = new UserBuilder()
  .withName('John Doe')
  .withEmail('john@example.com')
  .build();
```

## Coverage Structure

### Coverage Goals
```javascript
// jest.config.js or vitest.config.js
export default {
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/components/': {
      branches: 90,
      functions: 90
    },
    './src/utils/': {
      branches: 100,
      functions: 100
    }
  }
};
```

## Examples

### ✅ Well-Structured Test
```javascript
describe('ShoppingCart', () => {
  let mockProducts: Product[];
  
  beforeEach(() => {
    mockProducts = [
      createMockProduct({ id: '1', price: 10 }),
      createMockProduct({ id: '2', price: 20 })
    ];
  });
  
  describe('adding items', () => {
    it('should add item to empty cart', () => {
      const cart = new ShoppingCart();
      cart.addItem(mockProducts[0]);
      expect(cart.items).toHaveLength(1);
    });
    
    it('should increase quantity for existing item', () => {
      const cart = new ShoppingCart();
      cart.addItem(mockProducts[0]);
      cart.addItem(mockProducts[0]);
      expect(cart.items[0].quantity).toBe(2);
    });
  });
  
  describe('calculating total', () => {
    it('should calculate correct total', () => {
      const cart = new ShoppingCart();
      cart.addItem(mockProducts[0]);
      cart.addItem(mockProducts[1]);
      expect(cart.getTotal()).toBe(30);
    });
  });
});
```

## Rationale

### Why These Conventions

1. **Maintainability**: Organized tests are easier to update
2. **Discoverability**: Consistent structure aids navigation
3. **Coverage**: Clear organization reveals testing gaps
4. **Debugging**: Well-structured tests speed diagnosis
5. **Reusability**: Shared fixtures and helpers reduce duplication

### Benefits
- **Faster Development**: Reusable test utilities
- **Better Coverage**: Organized tests show what's missing
- **Easier Debugging**: Clear structure aids troubleshooting
- **Team Efficiency**: Everyone knows where things go
- **Confidence**: Comprehensive tests enable refactoring