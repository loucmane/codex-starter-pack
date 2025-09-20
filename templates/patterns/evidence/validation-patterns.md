---
id: validation-patterns
type: pattern
category: evidence
title: Validation Patterns
pattern_type: operational
complexity: moderate
dependencies:
  - patterns/evidence/evidence-patterns.md
related:
  - patterns/evidence/proof-patterns.md
version: 1.0.0
status: stable
---

# Validation Patterns

## Pattern Description
Approaches and methods for validating code, claims, evidence, and system behavior. These patterns ensure accuracy and correctness through systematic verification.

## Pattern Structure
1. Identify what needs validation
2. Determine validation criteria
3. Select validation method
4. Perform validation checks
5. Document validation results
6. Handle validation failures

## When to Use
- Verifying code correctness
- Validating evidence quality
- Checking claim accuracy
- Confirming system behavior
- Ensuring requirement compliance

## When NOT to Use
- Exploratory or creative tasks
- Hypothetical discussions
- Opinion-based assessments
- Time-critical emergencies

## Validation Types

### Code Validation
- **Syntax validation**: Code parses correctly
- **Type validation**: Types match expectations
- **Logic validation**: Algorithm correctness
- **Style validation**: Follows conventions
- **Test validation**: Tests pass

### Evidence Validation
- **Source validation**: Evidence from reliable source
- **Currency validation**: Evidence is current
- **Relevance validation**: Evidence supports claim
- **Completeness validation**: Sufficient evidence
- **Accuracy validation**: Evidence is correct

### Behavioral Validation
- **Functional validation**: Features work as expected
- **Performance validation**: Meets performance criteria
- **Security validation**: No vulnerabilities
- **Integration validation**: Components work together
- **User validation**: Meets user requirements

## Validation Methods

### Static Validation
Validation without execution:
1. Code review and inspection
2. Type checking
3. Linting and style checks
4. Documentation review
5. Configuration validation

### Dynamic Validation
Validation through execution:
1. Unit test execution
2. Integration testing
3. Performance testing
4. Security scanning
5. User acceptance testing

### Cross-Reference Validation
Multiple source verification:
1. Check multiple files
2. Verify across systems
3. Confirm with documentation
4. Validate with tests
5. Cross-check with logs

## Validation Patterns

### Claim Validation Pattern
**Purpose**: Verify assertions about the system

**Process**:
1. Parse claim into checkable components
2. For each component:
   - Identify validation method
   - Collect evidence
   - Verify evidence
   - Score confidence
3. Aggregate results
4. Determine overall validity

**Example**:
```
Claim: "The API uses JWT with refresh tokens"
Validation:
1. Check for JWT library ✓
2. Find token generation ✓
3. Locate refresh logic ✓
4. Verify token validation ✓
Result: Claim validated (4/4 checks passed)
```

### Code Change Validation Pattern
**Purpose**: Ensure code changes are correct

**Process**:
1. Identify change scope
2. Check syntax validity
3. Verify logic correctness
4. Ensure no breaking changes
5. Validate test coverage
6. Confirm style compliance

**Validation Checklist**:
- [ ] Syntax is valid
- [ ] Types are correct
- [ ] Logic is sound
- [ ] Tests still pass
- [ ] No regressions
- [ ] Follows conventions

### Evidence Quality Validation Pattern
**Purpose**: Ensure evidence is reliable

**Quality Criteria**:
1. **Specificity**: Evidence directly supports claim
2. **Recency**: Evidence is current (not outdated)
3. **Authority**: Source is authoritative
4. **Completeness**: Evidence tells whole story
5. **Verifiability**: Can be independently verified

**Scoring**:
- 5/5: High confidence
- 3-4/5: Moderate confidence
- 1-2/5: Low confidence
- 0/5: Invalid evidence

### Integration Validation Pattern
**Purpose**: Verify components work together

**Process**:
1. Identify integration points
2. Check interface compatibility
3. Verify data flow
4. Test error handling
5. Validate performance
6. Confirm security

**Common Checks**:
- API contracts match
- Data formats align
- Error propagation works
- Transactions complete
- Security context maintained

## Validation Workflows

### Pre-Commit Validation
Before code submission:
1. Run linters
2. Execute unit tests
3. Check formatting
4. Verify documentation
5. Validate dependencies

### Post-Implementation Validation
After feature completion:
1. Functional testing
2. Integration testing
3. Performance validation
4. Security review
5. User acceptance

### Continuous Validation
Ongoing checks:
1. Monitor system health
2. Track performance metrics
3. Check error rates
4. Validate data integrity
5. Verify security status

## Validation Results Handling

### Success Handling
When validation passes:
1. Document what was validated
2. Record validation method
3. Note confidence level
4. Proceed with confidence

### Failure Handling
When validation fails:
1. Identify specific failures
2. Document failure reasons
3. Suggest corrections
4. Block invalid operations
5. Request clarification

### Partial Success Handling
When some checks pass:
1. List passed validations
2. Highlight failures
3. Assess risk level
4. Recommend actions
5. Allow override with warning

## Common Validation Scenarios

### API Endpoint Validation
```
Validate: New REST endpoint
Checks:
- Route defined correctly
- Handler implemented
- Input validation present
- Auth/authz configured
- Tests written
- Documentation updated
```

### Database Change Validation
```
Validate: Schema migration
Checks:
- Migration syntax valid
- Rollback possible
- Data preserved
- Indexes maintained
- Constraints honored
- Performance acceptable
```

### Security Fix Validation
```
Validate: Security patch
Checks:
- Vulnerability addressed
- No new vulnerabilities
- Tests cover fix
- Performance maintained
- Backward compatible
- Documented properly
```

## Validation Anti-Patterns

1. **Validation after the fact**: Validate before proceeding
2. **Incomplete validation**: Check all aspects
3. **Ignoring failures**: Address all validation issues
4. **Over-validation**: Don't validate unnecessarily
5. **Manual validation only**: Automate where possible

## Validation Metrics

### Coverage Metrics
- Code coverage: % of code validated
- Test coverage: % of features tested
- Path coverage: % of paths checked

### Quality Metrics
- Pass rate: % of validations passing
- Confidence: Average confidence score
- Time to validate: Validation duration

### Risk Metrics
- Critical failures: High-severity issues
- Warning count: Medium-severity issues
- Tech debt: Validation bypassed

## Examples

### Good Validation Practice
```
Task: Update authentication
Validation:
1. Check existing auth works ✓
2. Verify new auth logic ✓
3. Test edge cases ✓
4. Validate security ✓
5. Confirm backward compatibility ✓
Result: Safe to proceed
```

### Poor Validation Practice
```
Task: Update authentication
Action: Made changes without testing
Result: Production authentication broken
```

## Related Patterns
- [Evidence Patterns](evidence-patterns.md) - Collecting evidence
- [Proof Patterns](proof-patterns.md) - Proof standards
- [Testing Patterns](../work-tracking/work-patterns.md) - Test approaches

## Handler References
Validation logic is embedded in various handlers rather than standalone