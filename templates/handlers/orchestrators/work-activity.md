---
id: work-activity
name: Work Activity
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "test"
  - "testing"
  - "implement"
  - "analyze"
  - "fix"
  - "document"
  - "new feature"
  - "work on"
  - "build"
  - "develop"
dependencies:
  - continue-work
  - start-new-work
tools: []
version: 1.0.0
---

#### Pattern: work-activity {#work-activity}
**Triggers**: test, testing, implement, analyze, fix, document, "new feature", "work on", build, develop
**Pre-conditions**: None (meta-pattern)
**Process**:
1. Check for active work folder in docs/ai/work-tracking/active/
2. If exists → Load WORKFLOWS.md#continue-work
3. If not → Load WORKFLOWS.md#start-new-work
4. Follow loaded handler
**Success**: Routed to appropriate work handler
**Failure**: Use generic work creation
**Examples**:
- "Let's test auth" → Routes to start-new-work
- "Continue testing" → Routes to continue-work
- "Fix the login bug" → Routes to start-new-work or continue-work