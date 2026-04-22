---
id: work-activity
name: Work Activity
title: Work Activity
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
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
2. If exists → Load templates/handlers/triggers/workflow/continue-work.md
3. If not → Load templates/handlers/triggers/development/start-new-work.md
4. Follow loaded handler
**Success**: Routed to appropriate work handler
**Failure**: Use generic work creation
**Examples**:
- "Let's test auth" → Routes to start-new-work
- "Continue testing" → Routes to continue-work
- "Fix the login bug" → Routes to start-new-work or continue-work

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/work-activity.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
