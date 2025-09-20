---
id: verify-claim
name: Verify Claim
role: operator
domain: analysis
stability: stable
triggers:
  - "prove X is true"
  - "verify that Y"
  - "confirm Z"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: verify-claim {#verify-claim}
**Triggers**: "prove X is true", "verify that Y", "confirm Z"
**Target Pattern**: Extract claim to verify
**Pre-conditions**: 
- Claim is specific and verifiable
- Code/documentation accessible
**Process**:
1. Parse claim into verifiable components
2. **PRIMARY**: Use Serena to find evidence:
   - Symbol definitions for code claims
   - Pattern search for implementation claims
   - Reference search for usage claims
3. Gather concrete file:line references
4. Present evidence with context
5. State confidence level
**Success**: Claim verified with evidence
**Failure**: Cannot verify, show what was checked
**Examples**:
- "prove the auth system uses JWT" → Find JWT imports/usage
- "verify all tests pass" → Run tests and show results