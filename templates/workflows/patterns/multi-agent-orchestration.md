---
id: multi-agent-orchestration
type: workflow-component
category: patterns
title: Intelligent Multi-Agent Orchestration
dependencies:
  - ./task-management.md
  - ../core/ultrathink-reference.md
related:
  - ./specialist-deployment.md
version: 1.0.0
status: stable
---
> **Codex Alignment:** Keep plan/tracker + Taskmaster in sync when orchestrating specialists (plan update = legacy TodoWrite, tracker review = legacy TodoRead). Sync via `python3 scripts/codex-task plan sync` before and after deployments.

# Intelligent Multi-Agent Orchestration

## Sequential Subtask Processing

When working on TaskMaster tasks, the AI processes subtasks sequentially with intelligent specialist deployment based on value-add analysis.

## How It Works

1. **TaskMaster Foundation**
   - Every task has subtasks (verified: all 32 tasks have them!)
   - Subtasks processed one at a time
   - Natural dependencies respected

2. **Intelligent Analysis per Subtask** (5-10 seconds)
   - Quick ultrathink for each subtask
   - Assess specialist value-add (not keywords)
   - Consider implicit requirements
   - Learn from past decisions

3. **Clear Deployment Rules**
   ```yaml
   Deploy Specialist When:
     - 3+ steps/subtasks → Review & implement together
     - Security/auth/payments → Always deploy
     - Accessibility requirements → Always deploy
     - High risk changes → Deploy for safety
     - Keywords: "design", "integrate", "optimize"
   
   Solo Work When:
     - 1-2 simple steps
     - Low risk changes (docs, styles, comments)
     - Clear single-file fixes
   ```

## Real-World Example Flow

### Task 7: Core Layout Components

```markdown
User: "Work on task 7"

AI: "Task 7: Core Layout Components has 7 subtasks. 
    Starting with 7.1: Create Semantic HTML Structure
    
    [Ultrathink: Basic HTML, foundation work, I can handle this]
    Creating semantic HTML structure..."
    ✅ Complete

AI: "Moving to 7.2: Implement Header Component
    
    [Ultrathink: Design + branding + navigation = 3+ concerns
     Keywords: "design" detected]
    This involves multiple design decisions. 
    Deploying UI specialist to review approach with you..."
    
    [UI Specialist works with focused context]
    
    "The UI specialist has completed the Header Component.
    
    📋 Ready for Your Testing:
    - Files: /components/Header.tsx, /styles/header.module.css
    - Run: pnpm dev
    - Focus: Responsive nav, mobile menu, theme toggle
    
    I'll pause here for your testing."

User: "Looks great! The mobile menu works perfectly."

AI: "Excellent! Moving to 7.3: Develop Mobile Navigation System
    
    [Ultrathink: Mobile patterns, responsive design, touch interactions
     Similar to previous - UI specialist continues]
    The UI specialist will continue with mobile navigation..."
```

## For Non-TaskMaster Work

When user doesn't reference a specific task:

```markdown
User: "Fix the authentication timeout bug"

AI: [No task ID, analyzing request]
    "Looking at this authentication bug...
    
    [Ultrathink: Auth timeout = potential security implications
     Security review value-add: ~80%]
    Since this touches authentication logic, I'll have a 
    security specialist review the fix. Starting now..."
```

## Progressive Learning

The system tracks patterns for continuous improvement:

```yaml
Learning Database:
  "Component Implementation" patterns:
    - With UI Specialist: avg 70% quality improvement
    - Solo: adequate for simple components
    - Decision: Deploy for complex UI work
  
  "Security Fixes" patterns:
    - With Security Specialist: caught 3 additional vulnerabilities
    - Solo: missed edge cases
    - Decision: Always deploy for auth-related work
```

## Specialist Deployment Protocol

When deploying a specialist for a subtask:

### 1. Create Focused Context Package

```yaml
Subtask Context:
  subtask_info:
    id: "7.2"
    title: "Implement Header Component"
    description: "Full description from TaskMaster"
  
  focused_files: ["/components/", "/styles/theme.ts"]  # Max 3
  specific_focus: "Foundation branding, responsive nav"
  previous_work: "7.1 created HTML structure"
  constraints: "15 minutes, use existing design system"
```

### 2. Deploy with Clear Purpose

```javascript
// Conceptual deployment (handled by AI)
await Task.deploy({
  specialist: "UI/UX",
  subtask: currentSubtask,
  context: focusedContext,
  sharedDocs: ["sessions/", "current-todo-section"]
});
```

### 3. Track Progress

```markdown
sessions/ Update:
- **[HH:MM]** - Starting subtask 7.2: Header Component
- **[HH:MM]** - 🧠 Analysis: UI expertise adds 70% value
- **[HH:MM]** - 🎨 UI Specialist deployed for design decisions
- **[HH:MM]** - ✅ Subtask 7.2 complete with professional UI
```

## MANDATORY Constraints for ALL Specialist Deployments

**CRITICAL**: Every Task tool deployment MUST include these constraints to prevent session corruption and tool misuse.

### Constraint Template (COPY THIS EXACTLY)

```
=== MANDATORY CONSTRAINTS ===
FORBIDDEN TOOLS:
- NEVER use zen, gemini, openai, or other MCP AI tools
- NEVER use claude-code-bridge 
- Only use tools explicitly listed below

FORBIDDEN ACTIONS:
- NEVER edit or read sessions/ (that's exclusively managed by the primary agent (Codex main loop))
- NEVER create work tracking files (that's the primary agent (Codex main loop)'s responsibility)
- NEVER make git commits unless explicitly requested
- NEVER modify .claude/ directory contents

ALLOWED TOOLS:
- Bash (for running commands)
- Read/Write/Edit (for file operations)
- Grep/Glob (for searching)
- [Add other specific tools needed for this task]

REQUIRED BEHAVIOR:
- Stay focused on the specific task given
- Report findings back clearly
- Include file paths and line numbers in responses
- Stop when task is complete
=== END CONSTRAINTS ===
```

### Example with Constraints

```javascript
Task("Implement authentication feature")
Prompt: `
Implement JWT authentication for the user login system.

TASK:
- Add JWT token generation
- Create middleware for validation
- Update routes to require auth
- Write tests

=== MANDATORY CONSTRAINTS ===
[Full constraint template here]
=== END CONSTRAINTS ===

SUCCESS CRITERIA:
- JWT tokens properly generated
- Middleware validates tokens
- Tests pass
`
```

### Monitoring for Violations

After specialist returns, check:
1. Did they use any forbidden tools?
2. Did they touch sessions/? (Critical violation)
3. Did they create work tracking files?
4. Did they stay within scope?

If violations occur:
- Document in tracker: "Specialist violated constraint: [specific violation]"
- Add clarification to future deployments
- Do NOT use work if sessions/ was modified

## Future Evolution Path

The system is designed to evolve:

1. **Current: Pure Sequential**
   - One subtask at a time
   - Full focus per specialist
   - Clear dependencies

2. **Future: Smart Grouping**
   - Identify independent subtasks
   - Process groups sequentially
   - Parallelize within groups

3. **Ultimate: Dynamic Optimization**
   - Real-time dependency analysis
   - Optimal execution planning
   - Maximum efficiency

## Integration Notes

- Works with plan/tracker + Taskmaster for task tracking
- Updates sessions/ with specialist deployments
- Creates testing checkpoints after each subtask
- Maintains context through orchestration