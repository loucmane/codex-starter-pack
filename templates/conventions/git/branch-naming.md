---
id: git-branch-naming
type: convention
category: git
title: Branch Naming Standards
applies_to: code
enforcement: required
dependencies:
  - commit-format
version: 1.0.0
status: stable
---

# Branch Naming Standards

## Convention
Branch names must follow a consistent format that indicates purpose, scope, and tracking information.

## Branch Name Format

### Standard Pattern
```
type/task-id-descriptive-name
```

### Components
- **type**: Branch purpose (feat, fix, refactor, etc.)
- **task-id**: Issue or task number (optional but recommended)
- **descriptive-name**: Clear description in kebab-case

## Branch Types

### Feature Branches
- **Pattern**: `feat/[task-id]-description`
- **Examples**: 
  - `feat/004-shadcn-ui-setup`
  - `feat/007-core-layout-components`
  - `feat/auth-system`
- **Purpose**: New features or enhancements

### Bug Fix Branches
- **Pattern**: `fix/[task-id]-description`
- **Examples**:
  - `fix/015-auth-timeout`
  - `fix/023-mobile-menu-close`
  - `fix/memory-leak`
- **Purpose**: Bug fixes and corrections

### Refactor Branches
- **Pattern**: `refactor/[task-id]-description`
- **Examples**:
  - `refactor/023-optimize-bundles`
  - `refactor/component-structure`
  - `refactor/031-extract-hooks`
- **Purpose**: Code restructuring without feature changes

### Documentation Branches
- **Pattern**: `docs/description`
- **Examples**:
  - `docs/api-documentation`
  - `docs/readme-update`
  - `docs/component-examples`
- **Purpose**: Documentation only changes

### Chore Branches
- **Pattern**: `chore/description`
- **Examples**:
  - `chore/update-dependencies`
  - `chore/ci-configuration`
  - `chore/lint-setup`
- **Purpose**: Maintenance and tooling

### Hotfix Branches
- **Pattern**: `hotfix/description`
- **Examples**:
  - `hotfix/critical-auth-bug`
  - `hotfix/production-crash`
  - `hotfix/data-corruption`
- **Purpose**: Urgent production fixes

### Test Branches
- **Pattern**: `test/description`
- **Examples**:
  - `test/claude-execution-engine`
  - `test/integration-suite`
  - `test/performance-benchmarks`
- **Purpose**: Testing and experimentation

## Examples

### ✅ Good Branch Names
```bash
# With task IDs
feat/004-user-authentication
fix/012-sidebar-responsive
refactor/008-api-client-optimization

# Without task IDs (when appropriate)
feat/dark-mode-support
fix/typo-in-header
docs/installation-guide

# Complex features
feat/015-multi-tenant-architecture
feat/023-real-time-notifications
refactor/042-monorepo-migration
```

### ❌ Bad Branch Names
```bash
# Too vague
feature-1                    # What feature?
fix-bug                      # Which bug?
update                       # Update what?

# Wrong format
feature/user_authentication  # Use kebab-case, not snake_case
FEAT/login                   # Types are lowercase
004-authentication           # Missing type prefix
user-auth                    # Missing type prefix

# Too long
feat/implement-user-authentication-with-oauth2-google-github-providers

# Personal branches
john-branch                  # Not descriptive
my-work                      # Not descriptive
test                        # Too generic
```

## Special Branches

### Protected Branches
```bash
main                         # Production code
master                       # Legacy production (avoid)
develop                      # Development integration
staging                      # Pre-production testing
```

### Release Branches
- **Pattern**: `release/version`
- **Examples**: `release/1.2.0`, `release/2.0.0-beta`

### Version Branches
- **Pattern**: `v1.x`, `v2.x`
- **Purpose**: Major version maintenance

## Branch Lifecycle

### Creation
```bash
# Create from main
git checkout main
git pull origin main
git checkout -b feat/004-new-feature

# Create from develop
git checkout develop
git pull origin develop
git checkout -b fix/015-bug-fix
```

### Naming Guidelines

#### Length
- **Ideal**: 2-5 words after type
- **Maximum**: 50 characters total
- **Minimum**: Clearly descriptive

#### Words
- Use kebab-case (words-separated-by-hyphens)
- Avoid abbreviations unless well-known
- Be specific but concise

#### Task IDs
- Include when available
- Format: 3-4 digit number
- Position: After type, before description

## Branch Management

### Cleanup
```bash
# Delete local branch
git branch -d feat/004-completed-feature

# Delete remote branch
git push origin --delete feat/004-completed-feature

# Prune deleted remote branches
git remote prune origin
```

### Listing
```bash
# List all local branches
git branch

# List all remote branches
git branch -r

# List branches with last commit
git branch -v

# List merged branches
git branch --merged
```

## Rationale

### Why These Conventions

1. **Type Prefix**: Immediately understand branch purpose
2. **Task IDs**: Link to issue tracking system
3. **Kebab Case**: Standard for URLs and Git
4. **Descriptive Names**: Self-documenting branches
5. **Consistent Format**: Easy sorting and filtering

### Benefits
- **Organization**: Branches grouped by type
- **Traceability**: Task IDs link to requirements
- **Clarity**: Purpose evident from name
- **Automation**: CI/CD can parse branch types
- **Cleanup**: Easy to identify stale branches