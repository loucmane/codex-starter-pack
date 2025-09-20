---
id: enforce-pre-flight
name: Enforce Pre-Flight
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "enforce conventions"
  - "make sure I check"
  - "prevent mistakes"
dependencies:
  - check-conventions-first
tools: []
version: 1.0.0
---

#### Handler: enforce-pre-flight {#enforce-pre-flight}
**Triggers**: "enforce conventions", "make sure I check", "prevent mistakes"
**Target Pattern**: System-wide enforcement request
**Pre-conditions**: 
- User wants stricter enforcement
- Patterns of violations identified
**Process**:
1. Acknowledge enforcement request
2. **PRIMARY**: List all pre-action checks:
   - Git → templates/conventions/#git-conventions
   - Files → templates/conventions/#naming-conventions
   - Code → templates/conventions/#code-conventions
   - Tools → TOOLS.md#mandatory-tool-router
   - Claims → Evidence-based approach
3. Create mental checklist
4. Commit to checking BEFORE acting
5. Report when conventions checked
**Success**: Systematic pre-checks established
**Failure**: Continuing without checks
**Examples**:
- "Stop making git mistakes" → Enforce git pre-checks
- "Always check first" → Universal pre-flight protocol