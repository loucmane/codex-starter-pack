---
id: directory-structure
type: convention
category: files
title: Project Directory Structure
applies_to: files
enforcement: recommended
dependencies:
  - file-organization
version: 1.0.0
status: stable
---

# Project Directory Structure

## Convention
Projects must follow a consistent directory structure that clearly separates concerns and scales with project growth.

## Standard Project Structure

### Monorepo Structure
```
project-root/
├── .claude/                 # AI system files
│   ├── templates/          # Template system
│   │   ├── handlers/       # Migrated handlers
│   │   ├── conventions/    # Convention modules
│   │   └── engine/        # Execution engine
│   ├── agents/             # AI agents
│   └── agent-outputs/      # Agent reports
├── .serena/                 # Serena memories
│   └── memories/           # Session memories
├── packages/                # Monorepo packages
│   ├── web/                # Web application
│   ├── ui/                 # UI component library
│   └── shared/             # Shared utilities
├── docs/                    # Documentation
│   ├── ai/                 # AI documentation
│   │   └── work-tracking/  # Work folders
│   └── api/                # API documentation
├── scripts/                 # Build and utility scripts
├── config/                  # Configuration files
└── sessions/               # Active session log
```

### Package Structure (packages/web)
```
packages/web/
├── src/
│   ├── components/         # React components
│   │   ├── ui/             # UI components
│   │   ├── layout/         # Layout components
│   │   └── features/       # Feature components
│   ├── pages/              # Page components
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API services
│   ├── store/              # State management
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript types
│   ├── styles/             # Global styles
│   └── constants/          # App constants
├── public/                  # Static assets
├── tests/                   # Test files
└── package.json             # Package config
```

## Folder Naming Conventions

### General Folders
- **Pattern**: `kebab-case`
- **Examples**: `user-profile`, `api-client`, `work-tracking`
- **Exception**: React component folders use PascalCase

### Component Folders
- **Pattern**: `PascalCase` for component folders
- **Examples**: `Button/`, `UserProfile/`, `HeaderNav/`
- **Contents**: Component file, tests, styles, types

### Work Tracking Folders
- **Pattern**: `YYYYMMDD-description-STATUS`
- **Examples**: 
  - `20250709-auth-implementation-ACTIVE`
  - `20250708-ui-setup-COMPLETE`
  - `20250707-planning-PAUSED`

## Special Directories

### .claude Directory
```
.claude/
├── templates/               # Template system
│   ├── handlers/           # Handler library
│   │   ├── triggers/       # User triggers
│   │   ├── orchestrators/  # Coordinators
│   │   └── operators/      # Executors
│   ├── conventions/        # Convention modules
│   └── engine/            # Core engine
├── agents/                 # AI agents
└── agent-outputs/          # Agent reports
    ├── template-scanner/   # Scanner outputs
    ├── template-migrator/  # Migration reports
    └── template-optimizer/ # Optimization reports
```

### Work Tracking Structure
```
docs/ai/work-tracking/
├── active/                  # Current work
│   └── 20250710-feature-ACTIVE/
│       ├── IMPLEMENTATION.md
│       ├── TRACKER.md
│       ├── CHANGELOG.md
│       ├── FINDINGS.md
│       ├── DECISIONS.md
│       ├── MEMORY-REFS.md
│       └── HANDOFF.md
├── completed/               # Finished work
├── paused/                  # On hold
├── abandoned/               # Stopped work
└── superseded/              # Replaced work
```

## Examples

### Good Structure
```
✅ Clear separation
packages/
  web/          # Web app
  mobile/       # Mobile app
  shared/       # Shared code
  ui/           # UI library

✅ Logical grouping
src/
  features/
    auth/       # Auth feature
    profile/    # Profile feature
    settings/   # Settings feature
```

## Anti-patterns

### Poor Structure
```
❌ Flat structure
src/
  Button.tsx
  Login.tsx
  api.ts
  utils.ts
  Profile.tsx
  types.ts

❌ Inconsistent naming
components/
  user-profile/    # kebab-case
  Button/          # PascalCase
  headerNav/       # camelCase

❌ Over-nesting
src/components/features/user/profile/settings/privacy/PrivacyToggle.tsx
```

## Directory Depth Guidelines

### Maximum Nesting
- **Recommended**: 3-4 levels deep
- **Maximum**: 5 levels deep
- **Exception**: Test files can mirror source depth

### When to Flatten
- Directory has only one file
- Excessive navigation required
- Logical grouping unclear

## Public vs Private

### Public Directories
- Export via index files
- Document public API
- Maintain backward compatibility

### Private Directories
- Prefix with underscore (optional)
- No external imports allowed
- Can change without notice

## Rationale

### Why These Conventions

1. **Scalability**: Structure grows with project
2. **Discoverability**: Predictable file locations
3. **Modularity**: Clear boundaries between features
4. **Maintainability**: Organized code easier to maintain
5. **Team Alignment**: Everyone knows the structure

### Benefits
- **Faster Navigation**: Know where files live
- **Clear Ownership**: Feature boundaries evident
- **Easy Onboarding**: New developers learn quickly
- **Better Tooling**: IDEs understand structure
- **Reduced Conflicts**: Clear separation of concerns