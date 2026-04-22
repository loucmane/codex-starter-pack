---
id: enforce-pre-flight
name: Enforce Pre-Flight
title: Enforce Pre-Flight
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/enforce-pre-flight.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
