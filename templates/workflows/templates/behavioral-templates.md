---
id: behavioral-templates
type: workflow-component
category: templates
title: Behavioral Templates
dependencies:
  - ../patterns/task-management.md
related:
  - ../protocols/universal-flight.md
version: 1.0.0
status: stable
---

# Behavioral Templates

Pre-composed tool sequences for common tasks. These templates optimize workflows by providing tested patterns for frequent operations.

## Quick Action Templates

### Start New Development Session

```markdown
1. Run session checks:
   - date "+%Y-%m-%d %H:%M %Z"
   - pwd
   - git status
   - git branch --show-current

2. Read context:
   - sessions/
   - Current todos
   - Recent Serena memory

3. Create session entry:
   - Update sessions/
   - Set goals
   - Note starting point

4. Begin work:
   - ULTRATHINK
   - Execute handler
```

### Implement New Feature

```markdown
1. Create work tracking:
   - Make folder in active/
   - Create 6 core files
   - Set up todos

2. Research phase:
   - Search existing patterns
   - Review similar implementations
   - Document findings

3. Implementation:
   - Create/modify files
   - Add tests
   - Update documentation

4. Validation:
   - Run tests
   - Create checkpoint
   - Get user feedback
```

### Debug Issue

```markdown
1. Gather evidence:
   - Error messages
   - Stack traces
   - Recent changes

2. Isolate problem:
   - Reproduce issue
   - Narrow scope
   - Identify root cause

3. Fix and verify:
   - Implement solution
   - Test thoroughly
   - Document fix
```

## Tool Sequence Templates

### Search and Replace Pattern

```bash
# 1. Find all occurrences
Serena search_for_pattern "oldPattern" --relative_path "src/"

# 2. Review locations
grep -n "oldPattern" [specific files]

# 3. Replace systematically
Edit [each file with occurrence]

# 4. Verify changes
Serena search_for_pattern "newPattern" --relative_path "src/"
```

### Code Analysis Pattern

```bash
# 1. Understand structure
find src -type f -name "*.tsx" | head -20

# 2. Analyze patterns
Serena analyze_codebase --focus "components"

# 3. Extract examples
Serena show_file_snippet "[key file]" --context

# 4. Document findings
Write "findings.md" [analysis results]
```

### Test Verification Pattern

```bash
# 1. Run test suite
npm test

# 2. Check coverage
npm run test:coverage

# 3. Verify specific area
npm test -- [specific test file]

# 4. Document results
Update tracker.md with test status
```

## Complex Workflow Templates

### Component Creation

```markdown
## Create New React Component

1. **Plan Structure**
   - Component name: [PascalCase]
   - Props interface
   - State requirements
   - Dependencies

2. **Create Files**
   ```
   components/
   ├── ComponentName/
   │   ├── index.tsx
   │   ├── ComponentName.tsx
   │   ├── ComponentName.module.css
   │   ├── ComponentName.test.tsx
   │   └── types.ts
   ```

3. **Implement Component**
   - Base structure
   - Props handling
   - Event handlers
   - Styling

4. **Add Tests**
   - Render test
   - Props test
   - Event test
   - Edge cases

5. **Integration**
   - Import in parent
   - Update exports
   - Test integration
```

### API Integration

```markdown
## Integrate External API

1. **Setup**
   - Install dependencies
   - Configure environment
   - Set up types

2. **Create Service Layer**
   ```typescript
   // services/api/[name].ts
   - Client setup
   - Auth handling
   - Error handling
   - Rate limiting
   ```

3. **Implement Hooks**
   ```typescript
   // hooks/use[Name].ts
   - Data fetching
   - Caching logic
   - Error states
   - Loading states
   ```

4. **Add Components**
   - Loading component
   - Error component
   - Data display
   - Refresh controls

5. **Testing**
   - Mock API calls
   - Test error cases
   - Test loading states
   - Integration tests
```

## Session Management Templates

### End Session Properly

```markdown
1. **Final Updates**
   - Run: date "+%Y-%m-%d %H:%M %Z"
   - Update sessions/ final status
   - Mark todos complete/pending

2. **Create Memory**
   - Serena write memory
   - Include work summary
   - Note blockers
   - Add init instructions

3. **Update Handoff**
   - Current state
   - Next steps
   - Known issues
   - Test results

4. **Commit**
   - Stage changes
   - Descriptive message
   - Push if needed

5. **User Message**
   - Completion summary
   - Init instructions
   - Next session start
```

### Resume After Compaction

```markdown
1. **Restore Context**
   - Read sessions/ fully
   - Check git status
   - Review todos

2. **Verify State**
   - Confirm last action
   - Check file states
   - Test still pass?

3. **Continue Work**
   - Pick up exact point
   - Don't redo work
   - Maintain style

4. **Document**
   - Note restoration
   - Continue logging
   - Update progress
```

## Quick Reference Commands

### Git Operations
```bash
gac "feat: [description]"     # Add all and commit
gs                           # Git status
gd                           # Git diff
gl                           # Git log pretty
```

### Testing
```bash
npm test                     # Run all tests
npm test -- --watch          # Watch mode
npm run test:coverage        # Coverage report
npm test [file]              # Specific test
```

### Development
```bash
npm run dev                  # Start dev server
npm run build                # Production build
npm run lint                 # Run linter
npm run format               # Format code
```

### Search
```bash
grep -r "pattern" .          # Recursive search
find . -name "*.tsx"         # Find files
rg "pattern" --type tsx      # Ripgrep search
```

## Template Selection Guide

Choose template based on:

1. **Task Type**
   - Feature → Implementation template
   - Bug → Debug template
   - Review → Analysis template

2. **Complexity**
   - Simple → Quick action
   - Medium → Tool sequence
   - Complex → Full workflow

3. **Frequency**
   - Common → Use template as-is
   - Rare → Adapt template
   - Novel → Create new template

## Creating New Templates

When you repeat a sequence 3+ times:

1. Document the pattern
2. Test the sequence
3. Add to this file
4. Include:
   - When to use
   - Step sequence
   - Success criteria
   - Common variations

## Remember

**Templates are starting points, not rigid rules.**

Adapt them based on:
- Current context
- Project requirements
- User preferences
- Lessons learned