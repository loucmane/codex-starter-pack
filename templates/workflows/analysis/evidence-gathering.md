---
id: evidence-gathering
type: workflow-component
category: analysis
title: Evidence Gathering Workflows
dependencies:
  - ../protocols/universal-flight.md
related:
  - ./claim-validation.md
  - ./analysis-workflows.md
version: 1.0.0
status: stable
---

# Evidence Gathering Workflows

## Core Principle

**"Every claim requires evidence, every assumption needs validation"**

The evidence-based analysis workflow ensures all technical decisions and claims are backed by actual data from the codebase, not assumptions or memory.

## When to Use Evidence-Based Analysis

### Required Scenarios

1. **Making Technical Claims**
   - "This component does X" → Show the code
   - "The system uses Y pattern" → Find examples
   - "Performance is Z" → Provide metrics

2. **Comparing Implementations**
   - Old vs new code
   - Different approaches
   - Framework migrations

3. **Debugging Issues**
   - Root cause analysis
   - Impact assessment
   - Regression detection

4. **Architecture Decisions**
   - Current state documentation
   - Change impact analysis
   - Migration planning

## Evidence Gathering Process

### Step 1: Identify Claims

Before making any statement:
1. Pause and identify what you're claiming
2. Ask: "What evidence would support this?"
3. Determine where to find that evidence

### Step 2: Gather Evidence

```bash
# For code structure claims
Serena: search_for_pattern "className=" --relative_path "components/"

# For implementation details
Serena: show_file_snippet "auth/middleware.ts" --start_line 50 --end_line 75

# For usage patterns
grep -r "useAuth" --include="*.tsx" | head -20

# For dependencies
cat package.json | jq '.dependencies'
```

### Step 3: Document Evidence

```markdown
## Analysis: Authentication Implementation

### Claim: "The app uses JWT tokens for authentication"

**Evidence**:
1. From `auth/config.ts` (lines 12-15):
   ```typescript
   export const authConfig = {
     tokenType: 'JWT',
     expiresIn: '24h',
     secret: process.env.JWT_SECRET
   }
   ```

2. From `middleware/auth.ts` (lines 34-41):
   ```typescript
   const token = jwt.verify(bearerToken, config.secret)
   ```

3. Usage in 12 components:
   - `components/Header.tsx`: Line 23
   - `pages/dashboard.tsx`: Line 45
   - [List all actual occurrences]

**Conclusion**: ✅ Confirmed - JWT implementation verified
```

## Evidence Types and Sources

### Code Evidence
- Direct file content
- Function implementations
- Import statements
- Configuration values

### Usage Evidence
- Grep results showing patterns
- Component references
- API calls
- Test coverage

### Performance Evidence
- Bundle size reports
- Lighthouse scores
- Runtime metrics
- Memory profiles

### Historical Evidence
- Git history
- PR descriptions
- Issue discussions
- Documentation

## Common Anti-Patterns

### ❌ Making Claims Without Evidence

**Wrong**:
"The header component probably uses flexbox for layout"

**Right**:
"The header component uses flexbox - verified in `Header.module.css` line 8: `display: flex`"

### ❌ Using Outdated Information

**Wrong**:
"Based on what I remember from earlier..."

**Right**:
"Current implementation (verified just now) shows..."

### ❌ Generalizing from Single Example

**Wrong**:
"All components use this pattern" (after seeing one)

**Right**:
"Found this pattern in 8 of 12 components: [list them]"

## Evidence-Based Debugging

### Problem Investigation Flow

1. **Reproduce Issue**
   ```bash
   # Run failing test
   npm test -- auth.test.ts
   # Capture exact error
   ```

2. **Trace Execution**
   ```bash
   # Find error origin
   grep -n "Error:" logs/test.log
   # Check related code
   ```

3. **Gather Context**
   ```bash
   # Recent changes
   git diff HEAD~5 -- auth/
   # Related issues
   ```

4. **Document Findings**
   ```markdown
   ## Bug Analysis: Auth Token Expiry
   
   ### Evidence Trail:
   1. Error occurs at: `auth/validate.ts:45`
   2. Root cause: Token expiry not checked
   3. Impact: 3 endpoints affected [list them]
   4. Fix: Add expiry validation
   ```

## Evidence Quality Checklist

- [ ] Is the evidence current? (not from memory)
- [ ] Is it specific? (file names, line numbers)
- [ ] Is it complete? (all relevant cases)
- [ ] Is it verifiable? (others can check)
- [ ] Is it documented? (saved for reference)

## Tools for Evidence Gathering

### Serena (Preferred)
- `search_for_pattern` - Find code patterns
- `show_file_snippet` - Get specific sections
- `analyze_codebase` - Statistical analysis

### Grep/Ripgrep
- Pattern matching across files
- Count occurrences
- Find usage examples

### Git
- Historical changes
- Blame for context
- Diff for comparisons

### Static Analysis
- Type checking results
- Linting reports
- Dependency graphs

## Integration with Other Workflows

- Use with Testing Workflows for validation
- Combine with Session Management for tracking
- Apply in Code Reviews for thorough analysis
- Essential for Architecture Documentation