---
id: docs-standards
type: convention
category: docs
title: General Documentation Format
applies_to: documentation
enforcement: required
dependencies:
  - comment-format
  - readme-format
version: 1.0.0
status: stable
---

# Documentation Standards

## Convention
All documentation must be clear, comprehensive, and follow consistent formatting to ensure knowledge is effectively shared.

## Documentation Types

### Code Documentation
- **Inline Comments**: Explain complex logic
- **Function Documentation**: JSDoc/TSDoc for public APIs
- **Module Documentation**: File-level overview
- **Type Documentation**: Interface and type descriptions

### Project Documentation
- **README.md**: Project overview and setup
- **API Documentation**: Endpoint descriptions
- **Architecture Docs**: System design decisions
- **Contributing Guide**: How to contribute

### Work Documentation
- **sessions/**: Active work sessions
- **TRACKER.md**: Task tracking
- **HANDOFF.md**: Session transitions
- **FINDINGS.md**: Discoveries and insights

## Markdown Standards

### Heading Hierarchy
```markdown
# Main Title (One per document)

## Major Section

### Subsection

#### Minor Heading

##### Rarely Used

###### Avoid if possible
```

### Code Blocks
````markdown
```language
// Always specify language for syntax highlighting
const example = 'code';
```

```bash
# Shell commands
pnpm install
```

```typescript
// TypeScript with proper highlighting
interface Example {
  value: string;
}
```
````

### Lists
```markdown
## Unordered Lists
- Main point
  - Sub-point (2 space indent)
  - Another sub-point
    - Nested point (avoid deep nesting)

## Ordered Lists
1. First step
2. Second step
   1. Sub-step (3 space indent for numbers)
   2. Another sub-step
3. Third step

## Task Lists
- [x] Completed task
- [ ] Pending task
- [ ] Future task
```

### Tables
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data     | Data     | Data     |
| Left     | Center   | Right    |

| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Text         | Text           | Text          |
```

## API Documentation

### Endpoint Documentation
```markdown
## GET /api/users/:id

Retrieve a single user by ID.

### Parameters
- `id` (string, required): User ID

### Query Parameters
- `include` (string, optional): Include related data
  - Values: `posts`, `comments`, `profile`

### Response
```json
{
  "id": "123",
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Errors
- `404`: User not found
- `401`: Unauthorized
```

## Function Documentation

### JSDoc Format
```javascript
/**
 * Calculates the total price including tax.
 * 
 * @description
 * This function takes a base price and tax rate, then calculates
 * the total price including tax. The tax rate should be provided
 * as a decimal (e.g., 0.1 for 10%).
 * 
 * @param {number} price - The base price before tax
 * @param {number} taxRate - The tax rate as a decimal
 * @returns {number} The total price including tax
 * 
 * @example
 * // Calculate price with 10% tax
 * const total = calculateTotal(100, 0.1);
 * console.log(total); // 110
 * 
 * @throws {Error} Throws if price is negative
 * @throws {Error} Throws if taxRate is negative
 * 
 * @since 1.0.0
 * @see {@link calculateDiscount} For discount calculations
 */
function calculateTotal(price, taxRate) {
  if (price < 0) throw new Error('Price cannot be negative');
  if (taxRate < 0) throw new Error('Tax rate cannot be negative');
  return price * (1 + taxRate);
}
```

### TypeScript Documentation
```typescript
/**
 * User data interface representing a system user.
 * @interface
 */
interface User {
  /** Unique user identifier */
  id: string;
  
  /** User's full name */
  name: string;
  
  /** User's email address (must be unique) */
  email: string;
  
  /** Account creation timestamp */
  createdAt: Date;
  
  /** Optional user profile */
  profile?: UserProfile;
}
```

## README Structure

### Standard README Template
```markdown
# Project Name

Brief description of what the project does.

## Features

- Key feature 1
- Key feature 2
- Key feature 3

## Installation

```bash
pnpm install
```

## Usage

```javascript
import { feature } from 'package';

feature.doSomething();
```

## API Reference

[Link to detailed API docs]

## Configuration

Environment variables and config options.

## Development

```bash
pnpm dev
pnpm test
pnpm build
```

## Contributing

See the repository contributing guide when one is present.

## License

MIT © [Author]
```

## Examples

### ✅ Good Documentation
```markdown
## User Authentication

This module handles user authentication using JWT tokens.

### How It Works

1. User submits credentials to `/auth/login`
2. Server validates credentials against database
3. If valid, server generates JWT token
4. Token is returned to client
5. Client includes token in subsequent requests

### Security Considerations

- Tokens expire after 24 hours
- Refresh tokens are stored securely
- All passwords are hashed using bcrypt

### Usage Example

```javascript
const token = await auth.login(email, password);
api.setAuthToken(token);
```
```

### ❌ Poor Documentation
```markdown
## Auth

Does authentication.

Use the login function to login.
```

## Documentation Principles

### Write for Your Audience
- **Users**: Focus on how to use
- **Developers**: Include implementation details
- **Contributors**: Explain architecture and decisions

### Keep It Current
- Update docs with code changes
- Remove outdated information
- Version documentation when needed

### Be Comprehensive but Concise
- Cover all important aspects
- Don't repeat obvious information
- Link to detailed docs when appropriate

### Use Examples
- Show real-world usage
- Include common patterns
- Demonstrate edge cases

## Rationale

### Why These Standards

1. **Discoverability**: Consistent structure aids navigation
2. **Completeness**: Templates ensure nothing missed
3. **Clarity**: Standards improve readability
4. **Maintenance**: Easier to keep current
5. **Onboarding**: New team members learn faster

### Benefits
- **Better Understanding**: Clear docs reduce confusion
- **Fewer Questions**: Comprehensive docs answer queries
- **Faster Development**: Good examples speed implementation
- **Knowledge Preservation**: Decisions and context captured
- **Professional Image**: Quality docs show quality code

## Work Tracking

- **2026-05-15 15:18 CEST** - [S:20260515|W:task80-production-deployment|H:reference-remediation|E:docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/scanner-2026-05-15-reference-circular-remediation.txt] Converted stale modularization references to valid navigation/prose during Task 80 production-readiness remediation.
