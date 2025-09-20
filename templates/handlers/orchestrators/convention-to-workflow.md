---
id: convention-to-workflow
name: Convention to Workflow Router
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "Convention violation requires workflow"
dependencies: []
tools:
  - correction workflow
  - timestamp workflow
  - evidence gathering
version: 1.0.0
---

#### Handler: convention-to-workflow {#convention-to-workflow}
**Triggers**: Convention violation requires workflow
**Target Pattern**: Fix process needed for violation
**Pre-conditions**: 
- Convention violation detected
- Workflow exists for correction
**Process**:
1. Identify violation type
2. Route to correction workflow
3. Guide through fix process
4. Verify convention compliance
**Success**: Violation corrected via workflow
**Failure**: Manual intervention needed
**Examples**:
- Wrong timestamp format → Route to timestamp workflow
- Missing evidence → Route to evidence gathering