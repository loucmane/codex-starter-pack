---
id: proof-requirement-patterns
type: pattern
category: evidence
title: Proof Requirement Patterns
pattern_type: operational
complexity: simple
dependencies:
  - patterns/evidence/evidence-patterns.md
  - patterns/evidence/validation-patterns.md
related:
  - patterns/selection/tool-selection.md
version: 1.0.0
status: stable
---

# Proof Requirement Patterns

## Pattern Description
Standards and requirements for what constitutes sufficient proof for different types of claims. These patterns define the level of evidence needed to support assertions with confidence.

## Pattern Structure
1. Classify claim type
2. Determine proof requirements
3. Define acceptance criteria
4. Specify evidence threshold
5. Document proof standard

## When to Use
- Establishing evidence requirements
- Determining proof sufficiency
- Setting validation standards
- Defining acceptance criteria
- Creating verification protocols

## When NOT to Use
- Informal discussions
- Hypothetical scenarios
- Creative brainstorming
- Opinion sharing

## Proof Levels

### Level 1: Basic Proof
**Sufficient for**: Simple factual claims
**Requirements**:
- Single source evidence
- Direct reference
- File:line citation

**Example**:
```
Claim: "The app uses Express.js"
Proof: package.json:12 shows "express": "^4.18.0"
Level: Basic proof sufficient
```

### Level 2: Standard Proof
**Sufficient for**: Implementation claims
**Requirements**:
- Multiple source evidence
- Active code usage
- Working implementation

**Example**:
```
Claim: "Authentication is implemented"
Proof: 
- auth.js contains login function
- middleware/auth.js has verification
- routes use auth middleware
Level: Standard proof achieved
```

### Level 3: Comprehensive Proof
**Sufficient for**: Architecture claims
**Requirements**:
- Documentation evidence
- Implementation evidence
- Test evidence
- Multiple examples

**Example**:
```
Claim: "System follows microservices architecture"
Proof:
- Architecture docs describe services
- Separate service directories exist
- Inter-service communication present
- Independent deployment configs
Level: Comprehensive proof provided
```

### Level 4: Exhaustive Proof
**Sufficient for**: Critical system claims
**Requirements**:
- Complete documentation
- Full implementation review
- Test coverage proof
- Performance metrics
- Security validation

**Example**:
```
Claim: "System is GDPR compliant"
Proof:
- Privacy policy implemented
- Data deletion capability
- Consent management system
- Audit logs present
- Encryption verified
Level: Exhaustive proof required
```

## Proof Requirements by Claim Type

### Technology Claims
**Claim type**: "Uses technology X"
**Proof required**:
- Package/dependency listing
- Import statements
- Actual usage in code
- Configuration files

**Threshold**: 2 out of 4 for basic, 3 out of 4 for strong

### Feature Claims
**Claim type**: "Has feature X"
**Proof required**:
- Feature implementation
- User interface/API endpoint
- Tests for feature
- Documentation

**Threshold**: Implementation + tests minimum

### Performance Claims
**Claim type**: "Performs at X level"
**Proof required**:
- Benchmark results
- Performance tests
- Monitoring data
- Configuration evidence

**Threshold**: Actual metrics required

### Security Claims
**Claim type**: "Is secure against X"
**Proof required**:
- Security implementation
- Validation logic
- Test coverage
- Audit results
- Best practices followed

**Threshold**: All evidence required

## Proof Standards

### Code Existence Proof
**Standard**: Code must be present and reachable
**Evidence**:
- File exists
- Function/class defined
- Not commented out
- Not in archived/deprecated folders

### Active Usage Proof
**Standard**: Code must be actively used
**Evidence**:
- Called by other code
- Referenced in routes/configs
- Tests exist and pass
- Recent modifications

### Correctness Proof
**Standard**: Implementation must be correct
**Evidence**:
- Logic is sound
- Tests pass
- No known bugs
- Handles edge cases

### Completeness Proof
**Standard**: Implementation must be complete
**Evidence**:
- All requirements met
- Full functionality present
- Error handling included
- Documentation complete

## Proof Evaluation Matrix

| Claim Type | Minimal Proof | Acceptable Proof | Strong Proof |
|------------|---------------|------------------|--------------|
| Library usage | Package.json entry | + Import statement | + Active usage |
| Feature exists | Code present | + Tests exist | + Documentation |
| Pattern followed | Some examples | Multiple examples | Consistent usage |
| Integration works | Config exists | + API calls | + E2E tests |
| Security measure | Implementation | + Validation | + Audit passed |

## Common Proof Patterns

### Dependency Proof Pattern
```
Claim: "Uses library X"
Required proof:
1. Check package.json/requirements ✓
2. Find import/require statements ✓
3. Locate actual usage ✓
Verdict: Proven if 2/3 present
```

### Implementation Proof Pattern
```
Claim: "Feature X is implemented"
Required proof:
1. Find feature code ✓
2. Verify it's connected ✓
3. Check for tests ✓
4. Find documentation ✓
Verdict: Proven if 3/4 present
```

### Architecture Proof Pattern
```
Claim: "Follows pattern X"
Required proof:
1. Find pattern structure ✓
2. Multiple implementations ✓
3. Consistent usage ✓
4. Documentation mentions ✓
Verdict: Proven if all present
```

## Insufficient Proof Handling

### When Proof is Insufficient
1. State what was found
2. Identify what's missing
3. Explain why insufficient
4. Suggest how to verify
5. Avoid unfounded claims

### Example Response
```
"I found partial evidence for [claim]:
- Found: [evidence found]
- Missing: [evidence needed]
- Cannot confirm without: [requirement]
- To verify, need to: [action]"
```

## Proof Documentation Format

### Standard Format
```
Claim: [What is being claimed]
Evidence Level: [Basic/Standard/Comprehensive/Exhaustive]
Proof Provided:
- [Evidence 1] (source:location)
- [Evidence 2] (source:location)
- [Evidence 3] (source:location)
Confidence: [High/Medium/Low]
Verdict: [Proven/Partially Proven/Not Proven]
```

### Example
```
Claim: System uses Redis for caching
Evidence Level: Standard
Proof Provided:
- Redis in package.json (package.json:23)
- Redis client initialized (cache/redis.js:5-10)
- Cache operations implemented (cache/operations.js:15-45)
Confidence: High
Verdict: Proven
```

## Anti-Patterns to Avoid

1. **Lowering standards**: Don't reduce requirements for convenience
2. **Assumption chains**: Don't build proof on assumptions
3. **Outdated proof**: Ensure evidence is current
4. **Cherry-picking**: Don't select only supporting evidence
5. **Overclaiming**: Don't claim more than proof supports

## Examples

### Good Proof Practice
```
User: "Does it use TypeScript?"
Process:
1. Check for .ts/.tsx files ✓
2. Find tsconfig.json ✓
3. Check package.json for typescript ✓
Response: "Yes, proven by TypeScript files, config, and dependency"
```

### Poor Proof Practice
```
User: "Is it scalable?"
Wrong: "Yes, it uses Node.js" (insufficient proof)
Right: "Scalability indicators found: load balancing config, clustering support, but would need performance tests for full proof"
```

## Related Patterns
- [Evidence Patterns](evidence-patterns.md) - Collecting evidence
- [Validation Patterns](validation-patterns.md) - Validating evidence
- [Tool Selection](../selection/tool-selection.md) - Tools for evidence gathering

## Handler References
Proof standards are embedded in various validation and analysis handlers