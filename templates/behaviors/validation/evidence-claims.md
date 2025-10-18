---
trigger: About to make claims about code, dependencies, or functionality
action: Gather evidence from actual code before making statements
blocks: Cannot make claims without proof
category: validation
enforcement: mandatory
version: 1.0.0
---

# Evidence Before Claims

## Trigger Conditions
This behavior fires whenever about to:
- State how code works
- Claim what a function does
- Assert dependencies or relationships
- Explain system behavior
- Make statements about functionality
- Answer "how does X work?"
- Claim something is broken/working
- State performance characteristics

## Required Action
```
BEFORE making any claim:

1. Identify the claim type:
   - Functionality claim → Need code evidence
   - Dependency claim → Need import/config evidence
   - Behavior claim → Need execution evidence
   - Performance claim → Need metrics evidence

2. Gather required evidence:
   mcp__serena__search_for_pattern --substring_pattern "evidence-check" --relative_path "templates/REGISTRY.md"
   
3. Use appropriate tool:
   - Serena: For code symbols and understanding
   - Grep: For text patterns and configs
   - Read: For specific file examination
   - Task: For complex multi-step validation

4. Collect concrete proof:
   - Line numbers
   - File paths
   - Actual code snippets
   - Config values
   - Test results

5. Only then make claim with evidence
```

## Blocking Gate
**CANNOT PROCEED** with claims until:
- Evidence gathering complete
- Proof points identified
- Line numbers available
- Actual code examined
- No assumptions made

## Satisfaction Criteria
✓ Claim has supporting evidence
✓ Evidence includes specific line numbers
✓ Code snippets provided
✓ File paths accurate
✓ No guessing or assumptions

## Evidence Types by Claim

### Functionality Claims
```
Claim: "The auth system uses JWT tokens"
Required Evidence:
- Import statements showing JWT library
- Code showing token generation
- Config with JWT settings
- Actual implementation lines
```

### Dependency Claims
```
Claim: "Component X depends on Service Y"
Required Evidence:
- Import statement in X
- Usage of Y in X's code
- Package.json dependency (if external)
- Actual call sites
```

### Behavior Claims
```
Claim: "The function validates input"
Required Evidence:
- Validation code in function
- Test cases showing validation
- Error handling for invalid input
- Specific validation logic
```

### Performance Claims
```
Claim: "This approach is faster"
Required Evidence:
- Benchmark results
- Complexity analysis
- Profiling data
- Comparative measurements
```

## Example Workflows

### ❌ Wrong Approach
```
User: "How does authentication work?"
AI: "The system uses JWT tokens with refresh tokens"
Problem: No evidence gathered, just assumed
```

### ✅ Correct Approach
```
User: "How does authentication work?"
AI:
1. Search: mcp__serena__find_symbol --symbol_name "authenticate"
2. Found: auth.js:45-67 implements authentication
3. Evidence: 
   - Line 47: `const token = jwt.sign(payload, secret)`
   - Line 52: `const refreshToken = generateRefreshToken()`
4. Response: "Authentication uses JWT (auth.js:47) with refresh tokens (auth.js:52)"
```

### Complex Evidence Gathering
```
User: "Why is login failing?"
AI:
1. Search for login function
2. Find login at auth/login.js:23
3. Read actual implementation
4. Find validation at line 28
5. Check error handling at line 35
6. Evidence: "Login fails due to validation check at login.js:28 which requires email format"
```

## Common Claims Requiring Evidence

| Claim Type | Required Evidence |
|------------|------------------|
| "X uses Y" | Import statements, usage sites |
| "X is broken" | Error messages, failing tests |
| "X works like..." | Actual implementation code |
| "X depends on..." | Package.json, imports, configs |
| "X is configured to..." | Config files, environment vars |
| "Tests cover X" | Test files, test descriptions |
| "X performs better" | Benchmarks, metrics, profiling |

## Tools for Evidence Gathering

### Serena (Preferred for Code)
```bash
mcp__serena__find_symbol --symbol_name "functionName"
mcp__serena__get_call_graph --symbol_name "functionName"
mcp__serena__search_semantic --query "authentication logic"
```

### Grep (For Patterns)
```bash
Grep --pattern "import.*jwt" --type js
Grep --pattern "error|fail|throw" --path src/auth
```

### Read (For Specific Files)
```bash
Read --file_path "src/auth/config.js"
Read --file_path "package.json"
```

## Cross-References
- [Evidence check pattern](../../templates/patterns/evidence/evidence-patterns.md#evidence-check-pattern)
- [TOOLS.md#tool-selection-matrix](../../templates/TOOLS.md)
- [work-tracking/update-tracker.md](../work-tracking/update-tracker.md) - Document findings

## Error Cases
- **Can't find evidence**: State "Unable to verify, no evidence found"
- **Conflicting evidence**: Present both with line numbers
- **Partial evidence**: Qualify claim as "appears to" or "partially"
- **No access**: State "Cannot examine, file not accessible"

## Special Considerations

### When Evidence is Implied
Even obvious claims need evidence:
- "React component" → Show JSX return
- "Uses TypeScript" → Show .ts extension or types
- "Async function" → Show async keyword

### When Multiple Sources Needed
Some claims require multiple evidence points:
- System behavior → Code + tests + configs
- Performance → Implementation + benchmarks
- Dependencies → Imports + package.json + usage

### When Evidence is Negative
Proving something doesn't exist:
- Search performed with no results
- All relevant files checked
- Document search parameters used

## Why This Gate Exists
- Prevents misinformation
- Builds trust through transparency
- Enables verification
- Catches incorrect assumptions
- Supports debugging with facts
- Creates traceable analysis

## Remember
**No claim without evidence - every statement must be backed by actual code!**