# Development Conventions & Standards

This file has been modularized. All conventions are now organized in `templates/conventions/`

> **Migration Notice**: 
> - All handlers have been migrated to `templates/handlers/`
> - All conventions have been extracted to `templates/conventions/`
> - This file now serves as an index to the modular convention system

## 📁 Module Organization

### Naming Conventions
- [File Naming](conventions/naming/files.md) - File naming standards (PascalCase, camelCase, kebab-case)
- [Variable Naming](conventions/naming/variables.md) - Variable and constant conventions
- [Function Naming](conventions/naming/functions.md) - Function and method naming patterns

### File Organization  
- [General Organization](conventions/files/organization.md) - File structure and organization principles
- [Special Files](conventions/files/special-files.md) - sessions/, TRACKER.md, HANDOFF.md rules
- [Directory Structure](conventions/files/directory-structure.md) - Project layout standards

### Git Conventions
- [Commit Format](conventions/git/commit-format.md) - gac format and commit messages
- [Branch Naming](conventions/git/branch-naming.md) - Branch naming standards
- [PR Conventions](conventions/git/pr-conventions.md) - Pull request format

### Code Style
- [JavaScript](conventions/code-style/javascript.md) - JS-specific conventions
- [TypeScript](conventions/code-style/typescript.md) - TS-specific conventions
- [General](conventions/code-style/general.md) - Language-agnostic style rules

### Documentation
- [Standards](conventions/docs/documentation-standards.md) - Documentation format
- [Comments](conventions/docs/comment-format.md) - Code comment style
- [README](conventions/docs/readme-format.md) - README format standards

### Testing
- [Test Naming](conventions/testing/test-naming.md) - Test file and function naming
- [Test Structure](conventions/testing/test-structure.md) - Test organization patterns

### Work Tracking
- [Folder Structure](conventions/work-tracking/folder-structure.md) - Work folder format
- [TRACKER Format](conventions/work-tracking/tracker-format.md) - Tracker file standards
- [HANDOFF Format](conventions/work-tracking/handoff-format.md) - Handoff documentation

### Timestamps
- [Format Rules](conventions/timestamps/format-rules.md) - Timestamp formats and commands
- [Usage Patterns](conventions/timestamps/usage-patterns.md) - When and where to use timestamps

## 🚨 Critical Rules

1. **NEVER type timestamps manually** - Always use `date` command
2. **ALWAYS use pnpm** - Never npm or yarn
3. **Use gac for commits** - With single quotes inside messages
4. **Check conventions BEFORE acting** - Not after
5. **Evidence-based claims only** - No unsupported statements

## Quick Command Reference

```bash
# Timestamps
date "+%Y-%m-%d %H:%M %Z"  # Full timestamp
date +%Y%m%d                # Folder dates
date '+%H:%M'               # Time only

# Git
gac "type: message with 'single quotes' inside"

# Package Manager
pnpm install                # NEVER npm or yarn
```

## Handler Migration Notice

All convention enforcement handlers have been migrated to the handler system:
- Code style handlers → `templates/handlers/operators/development/`
- Git convention handlers → `templates/handlers/operators/git/`  
- Documentation handlers → `templates/handlers/operators/docs/`
- Convention orchestrators → `templates/handlers/orchestrators/`

## See Also

- [Domain Workflows](templates/workflows/domain/README.md) - Complete workflow documentation
- [REGISTRY.md](REGISTRY.md) - Handler registry
- [BUILDING-BETTER.md](BUILDING-BETTER.md) - Creating new conventions

---

**Remember**: Conventions create consistency. When in doubt, check the relevant module!