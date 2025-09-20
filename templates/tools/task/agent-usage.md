---
id: agent-usage
type: tool-guide
category: task
title: Task Tool Agent Deployment Guide
version: 1.0.0
description: Intelligent delegation and specialist deployment patterns
status: stable
tools: [Task]
---

# Task Tool Agent Deployment Guide

## Overview

The Task tool is a built-in Claude capability (not MCP) that enables intelligent delegation to specialist agents. It processes work sequentially with value-based deployment decisions.

## Core Philosophy

Process tasks one at a time with intelligent specialist deployment based on value-add analysis, not keywords. Every complex task benefits from focused expertise.

## How It Works

### 1. Task Analysis

```yaml
Read Task Structure:
  - Identify subtasks
  - Review dependencies
  - Plan sequential approach
  - Estimate complexity
```

### 2. Sequential Processing

```yaml
For Each Subtask:
  - Quick ultrathink analysis (5-10 seconds)
  - Assess specialist value-add
  - Deploy if significant improvement expected
  - Complete before moving to next
```

### 3. Deployment Decision Matrix

```yaml
Decision Thresholds:
  >60% improvement: Auto-deploy specialist
  30-60%: Quick user suggestion
  <30%: Handle directly

Value Factors:
  - Required expertise domains
  - Quality improvement potential
  - Time/value tradeoff
  - Historical success patterns
```

## Specialist Context Package

### Standard Context Structure

```yaml
Specialist Context:
  subtask_info:
    id: "7.2"
    title: "Implement Header Component"
    description: [Full description]
  
  focus: "Foundation branding, navigation UX"
  files: ["/components/", "/styles/theme.ts"]  # Max 3 files
  constraints: "15 minutes, use design system"
  
  shared_state:
    session: "Current sessions/ section"
    previous_work: "7.1 completion notes"
    testing_required: true
```

## Real-World Examples

### Example 1: Component Development

```markdown
User: "Work on task 7"

AI: Task 7: Core Layout Components (7 subtasks)
    Starting with 7.1: Create Semantic HTML Structure
    
    [Ultrathink: Basic HTML, no specialist needed]
    Implementing semantic structure...
    
    Moving to 7.2: Implement Header Component
    [Ultrathink: Visual design, UX patterns - 70% value-add]
    Deploying UI specialist...
    
    📋 Ready for Testing:
    - Files: /components/Header.tsx
    - Run: pnpm dev
    - Test: Navigation, mobile menu
```

### Example 2: Security Implementation

```markdown
User: "Implement authentication"

AI: Breaking down authentication work...
    
    Subtask 1: Design auth flow
    [Ultrathink: Security critical - 85% value-add]
    Deploying security specialist...
    
    Specialist implementing OAuth2 flow...
    
    📋 Security Checkpoint:
    - Review: /lib/auth.ts
    - Test: Login flow, token handling
    - Verify: CSRF protection
```

## Deployment Patterns

### Pattern 1: Expertise-Based

```yaml
High Value Specialists:
  UI/UX: Component design, user flows
  Security: Auth, encryption, validation
  Performance: Optimization, caching
  Accessibility: ARIA, keyboard nav
  Testing: Test coverage, edge cases
```

### Pattern 2: Complexity-Based

```yaml
Complexity Triggers:
  Simple (No specialist):
    - Basic file operations
    - Simple config changes
    - Documentation updates
  
  Medium (Consider specialist):
    - Component implementation
    - API endpoints
    - State management
  
  Complex (Deploy specialist):
    - Architecture decisions
    - Security implementations
    - Performance optimization
```

### Pattern 3: Risk-Based

```yaml
Risk Assessment:
  High Risk (Always deploy):
    - Payment processing
    - User authentication
    - Data encryption
  
  Medium Risk (Usually deploy):
    - API integrations
    - Database operations
    - State mutations
  
  Low Risk (Rarely deploy):
    - Static content
    - Style changes
    - Comments/docs
```

## Testing Integration

### Testing Checkpoints

```yaml
After Each Specialist:
  1. Specialist completes work
  2. AI creates test checkpoint
  3. User performs testing
  4. Feedback incorporated
  5. Next subtask begins
```

### Checkpoint Format

```markdown
✅ Implemented: [Subtask name]

📋 Ready for Your Testing:
- Files: [Modified files list]
- Run: [Test command]
- Focus: [What to test]
- Notes: [Specialist insights]
```

## Progressive Learning

### Pattern Recognition

```yaml
Learning Database:
  "Header Component" + UI Specialist:
    outcomes: [excellent, excellent, good]
    avg_time: 12 minutes
    value_delivered: high
  
  "Basic HTML" + Solo:
    outcomes: [good, good, excellent]
    avg_time: 8 minutes
    value_delivered: appropriate
```

### Decision Evolution

```yaml
Historical Success:
  - Similar pattern detected
  - Previous specialist success: 90%
  - Auto-deploy confidence: High
  - Skip user confirmation
```

## Context Optimization

### Good Context Package

```yaml
Optimized:
  files: ["/lib/auth.ts", "/api/oauth/*"]  # Specific
  focus: "Token storage and CSRF"          # Focused
  constraints: "15 min, use Auth0"         # Clear
  shared_docs: ["sessions/", "auth.md"]   # Relevant
```

### Bad Context Package

```yaml
Poor:
  files: ["/**/*.ts"]            # Too broad
  focus: "Fix authentication"    # Too vague
  constraints: "Make it work"    # No bounds
  shared_docs: ["*"]             # Everything
```

## Communication Patterns

### Clear Deployment Reasoning

```markdown
"This involves [specific expertise]. Deploying [specialist] because:
- Requires deep knowledge of [domain]
- Historical success rate: X%
- Expected improvement: Y%"
```

### Progress Updates

```markdown
"Specialist working on [subtask]...
[Time elapsed: X minutes]
[Progress: implementing core logic]"
```

## Best Practices

### DO:
✓ Process subtasks sequentially
✓ Provide focused context
✓ Create testing checkpoints
✓ Track deployment patterns
✓ Learn from outcomes

### DON'T:
❌ Deploy multiple specialists simultaneously
❌ Provide entire codebase context
❌ Skip testing checkpoints
❌ Deploy for <30% improvement
❌ Ignore user preferences

## Anti-Patterns to Avoid

### ❌ Parallel Overwhelm
```
Wrong: Deploy 5 specialists at once
Right: Sequential processing with focus
```

### ❌ Keyword-Only Decisions
```
Wrong: "See 'auth' so deploy security"
Right: Analyze actual complexity and risk
```

### ❌ Context Overload
```
Wrong: Give specialist entire project
Right: Give 3 relevant files maximum
```

## Integration Examples

### With TaskMaster

```python
# 1. Get task from TaskMaster
mcp__taskmaster-ai__get_task --id="7"

# 2. Process subtasks sequentially
For each subtask:
  - Analyze with ultrathink
  - Deploy Task if valuable
  - Update TaskMaster status
```

### With TodoWrite

```python
# 1. Break down with TodoWrite
TodoWrite: Main task components

# 2. Process each TODO
For each TODO:
  - Assess specialist value
  - Deploy if beneficial
  - Update TODO status
```

## Quick Reference

| Scenario | Action |
|----------|--------|
| UI component | Deploy UI specialist (60-80% value) |
| Security feature | Deploy security specialist (80-90% value) |
| Simple config | Handle directly (<30% value) |
| Performance issue | Deploy performance specialist (50-70% value) |
| Unknown tech | Deploy research specialist (60-75% value) |
| Basic HTML | Handle directly (10-20% value) |
| Complex refactor | Deploy architecture specialist (70-85% value) |