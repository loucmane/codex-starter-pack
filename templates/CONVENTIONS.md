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
- [Commit Format](conventions/git/commit-format.md) - direct Git execution by default, explicit-only GAC output, and commit messages
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
3. **Use direct Git execution for delegated Git work** - `gac` output is explicit-request or auth-fallback only
4. **Check conventions BEFORE acting** - Not after
5. **Evidence-based claims only** - No unsupported statements

## Quick Command Reference

```bash
# Timestamps
date "+%Y-%m-%d %H:%M %Z"  # Full timestamp
date +%Y%m%d                # Folder dates
date '+%H:%M'               # Time only

# Git
git add -A
git commit -m "type(scope): concise summary" -m "Summary:
- Concrete change

Work tracking: YYYYMMDD-folder-ACTIVE"
git push -u origin <branch>

# Response modes
direct-git-execution   # default when delegated and auth is available
full-gac-command       # only when the user explicitly asks for "the gac"
message-payload-only   # only when the user asks for a message/payload
auth-refresh-required  # when SSH/GPG cache is expired

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
- [Extending the Template System](templates/integration/guides/extending-templates.md#extending-the-template-system) - Creating new conventions

---

## Progress Log

- **2026-05-07 14:05 CEST** — [S:20260507|W:task107-direct-git-execution-mode|H:templates/CONVENTIONS.md|E:docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/TRACKER.md] Updated the convention index so direct Git execution is the default and `full-gac-command`, `message-payload-only`, and `auth-refresh-required` are explicit response modes.

**Remember**: Conventions create consistency. When in doubt, check the relevant module!
