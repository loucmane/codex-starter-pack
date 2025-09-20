---
id: git-pr-conventions
type: convention
category: git
title: Pull Request Format and Standards
applies_to: code
enforcement: recommended
dependencies:
  - branch-naming
  - commit-format
version: 1.0.0
status: stable
---

# Pull Request Conventions

## Convention
Pull requests must provide clear context, follow a standard template, and facilitate efficient code review.

## PR Title Format

### Structure
```
type: Brief description of changes
```

### Examples
```
feat: Add user authentication with OAuth2
fix: Resolve memory leak in sidebar component
refactor: Extract shared hooks to separate module
docs: Update API documentation with examples
```

## PR Template

### Standard Template
```markdown
## Description
Brief summary of what this PR does and why.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Changes Made
- Bullet point list of specific changes
- Include file paths for major changes
- Highlight any architectural decisions

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No console errors

### Test Coverage
- Previous coverage: X%
- New coverage: Y%

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review
- [ ] I have commented complex code
- [ ] I have updated documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests for my changes
- [ ] All new and existing tests pass

## Related Issues
Closes #123
Relates to #456

## Additional Notes
[Any additional context or notes for reviewers]
```

## PR Size Guidelines

### Ideal PR Size
- **Lines changed**: < 400 lines
- **Files changed**: < 20 files
- **Review time**: < 1 hour

### When to Split PRs
- Changes exceed 500 lines
- Multiple unrelated features
- Mixed refactoring and features
- Complex changes needing staged review

## Review Process

### Author Responsibilities
1. **Self-review** before requesting review
2. **Provide context** in description
3. **Respond promptly** to feedback
4. **Update PR** based on review
5. **Resolve conflicts** promptly

### Reviewer Guidelines
1. **Review promptly** (within 24 hours)
2. **Be constructive** in feedback
3. **Focus on**:
   - Logic errors
   - Performance issues
   - Security concerns
   - Code style consistency
   - Test coverage

## Examples

### ✅ Good PR
```markdown
## Title
feat: Implement user dashboard with widgets

## Description
Adds a new user dashboard featuring customizable widgets for displaying user statistics, recent activity, and quick actions.

## Changes Made
- Created `Dashboard` component with grid layout
- Added 5 widget components (Stats, Activity, QuickActions, etc.)
- Integrated with existing user API
- Added responsive design for mobile

## Testing
- [x] Added unit tests for all components
- [x] Tested on Chrome, Firefox, Safari
- [x] Verified mobile responsiveness
```

### ❌ Poor PR
```markdown
## Title
Updates

## Description
Fixed some stuff and added new features

## Changes Made
Lots of changes to various files

## Testing
It works on my machine
```

## Commit Organization

### Atomic Commits
- Each commit should be one logical change
- Commits should be able to be reverted independently
- Squash WIP commits before merging

### Commit Grouping
```bash
# Good: Logical progression
feat: Add dashboard layout component
feat: Add widget base component
feat: Implement stats widget
feat: Implement activity widget
test: Add dashboard tests
docs: Update dashboard documentation

# Bad: Mixed concerns
WIP: stuff
more changes
fixed things
final changes
```

## Branch Protection Rules

### Required Checks
- All CI/CD checks must pass
- Code coverage maintained or improved
- No merge conflicts
- Approved by required reviewers

### Merge Strategies
- **Squash and merge**: For feature branches
- **Merge commit**: For release branches
- **Rebase and merge**: For small fixes

## Draft PRs

### When to Use
- Work in progress needing early feedback
- Architectural decisions need validation
- Complex features need incremental review

### Converting to Ready
- All tests passing
- Documentation complete
- Self-review done
- Ready for final review

## PR Labels

### Common Labels
- `ready-for-review`: Author completed, needs review
- `work-in-progress`: Still being developed
- `needs-changes`: Review requested changes
- `blocked`: Waiting on external dependency
- `priority-high`: Urgent review needed
- `breaking-change`: Contains breaking changes

## Merge Checklist

### Before Merging
- [ ] All review comments addressed
- [ ] CI/CD checks passing
- [ ] No merge conflicts
- [ ] Documentation updated
- [ ] CHANGELOG updated (if needed)
- [ ] Version bumped (if needed)

## Rationale

### Why These Conventions

1. **Clear Context**: Reviewers understand changes quickly
2. **Efficient Review**: Structured format speeds review
3. **Quality Gates**: Checklists ensure completeness
4. **Traceability**: Links to issues and requirements
5. **Knowledge Sharing**: PRs document decisions

### Benefits
- **Faster Reviews**: Clear structure reduces back-and-forth
- **Better Quality**: Checklists catch issues early
- **Documentation**: PRs serve as change documentation
- **Learning**: Team learns from PR discussions
- **Consistency**: Standard format across team