---
id: universal-flight-protocol
type: workflow-component
category: protocols
title: Universal Flight Protocol
dependencies: []
related:
  - ../core/ultrathink-reference.md
  - ../patterns/task-management.md
version: 1.0.0
status: stable
---

# Universal Flight Protocol

**CRITICAL**: This protocol is MANDATORY for ALL operations. It ensures consistent quality and prevents common errors.

## 🛫 PRE-FLIGHT (Before ANY Action)

1. **STATE**: "I'm about to [specific action]"
2. **CHECK**: Which workflow/convention applies? (State it out loud)
3. **TOOLS**: Need a tool? → Check [Tool Router](../../TOOLS.md#decision-router) FIRST!
4. **VERIFY**: Required tools ready? Dependencies checked?
5. **ULTRATHINK**: Deploy for non-trivial tasks

## ✈️ DURING FLIGHT (While Executing)

1. **FOLLOW**: The workflow/convention you identified
2. **TRACK**: Update todos in real-time
3. **VERIFY**: Check outputs match expectations
4. **DOCUMENT**: Note any deviations or discoveries

## 🛬 POST-FLIGHT (After Completion)

1. **REVIEW**: Did I follow the stated workflow?
2. **LEARN**: What errors did I make? Add to prevention list
3. **UPDATE**: Mark todos complete, update progress logs
4. **IMPROVE**: If workflow needs updates, do it NOW

## 🚨 ABORT PROCEDURES

- Lost? → State "I'm lost" and re-read relevant workflow
- Error? → Check Error Prevention in conventions
- Unsure? → Ask user rather than guess
- No workflow exists? → Create one using meta-flow

## Flight Protocol Examples

### Example 1: Updating tracker.md
```
PRE-FLIGHT: "I'm about to update tracker.md"
CHECK: "Checking templates/conventions/ for documentation standards"
TOOLS: "Need timestamp → Tool Router says use date command"
VERIFY: "Ready to proceed"
ACTION: Run date "+%Y-%m-%d %H:%M %Z"
```

### Example 2: Writing new component
```
PRE-FLIGHT: "I'm about to create a Button component"
CHECK: "Checking templates/conventions/ for component patterns"
VERIFY: "Need forwardRef pattern, PascalCase naming"
ULTRATHINK: "Deploying to analyze existing patterns"
```

### Example 3: Making a claim
```
PRE-FLIGHT: "I'm about to compare code structures"
CHECK: "Need Evidence-Based Analysis flow"
VERIFY: "Must gather actual data, not assumptions"
ACTION: Use Serena to extract specific examples
```

## Integration Notes

- This protocol applies to EVERY action taken during development
- It prevents common errors by forcing pre-flight checks
- It ensures proper tool selection through the Tool Router
- It creates a learning loop through post-flight review

## Work Tracking

- **2026-05-15 15:18 CEST** - [S:20260515|W:task80-production-deployment|H:reference-remediation|E:docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/scanner-2026-05-15-reference-circular-remediation.txt] Converted stale modularization references to valid navigation/prose during Task 80 production-readiness remediation.
