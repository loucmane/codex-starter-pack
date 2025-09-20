---
id: resolve-work-void
name: Resolve Work VOID
role: operator
domain: workflow
stability: stable
triggers:
  - "W = VOID"
  - "no work context"
  - "work unclear"
  - "VOID→workflows"
dependencies:
  - start-new-work
tools: []
version: 1.0.0
---

#### Handler: resolve-work-void {#resolve-work-void}
**Triggers**: "W = VOID", "no work context", "work unclear", "VOID→workflows"
**Target Pattern**: Missing work context in ULTRATHINK
**Pre-conditions**: 
- ULTRATHINK attempted
- W value is VOID
- Active work folders accessible
**Process**:
1. Analyze user request to determine domain:
   - Implementation/feature → Development work
   - Bug/fix/error → Problem solving
   - Search/find/explore → Investigation
   - Review/check → Review work
   - Plan/design → Planning work
2. Check active work folders:
   - List all folders in work-tracking/active/
   - Match request domain to folder names
   - If direct match → W = folder-name
3. Handle special states:
   - Search/analysis requests → W = "investigating"
   - Code/PR reviews → W = "reviewing"
   - Architecture/design → W = "planning"
4. If no match found:
   - Output: "No active work context for this request"
   - Route to appropriate handler:
     - New feature → start-new-work
     - Bug fix → start-new-work with bug context
     - General question → W = "investigating"
5. Return valid W value
**Success**: Valid work context obtained
**Failure**: Cannot determine context
**Examples**:
- "Fix login bug" with no bug folder → Routes to start-new-work
- "Find all getUserData calls" → W = "investigating"
- "Plan caching strategy" → W = "planning"
- "Continue with tests" + test folder exists → W = "test-implementation"