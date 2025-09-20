---
id: test-checkpoints
type: workflow-component
category: testing
title: User Testing Checkpoints
dependencies:
  - ../patterns/task-management.md
  - ../session/lifecycle.md
related:
  - ./simulation-testing.md
  - ./validation-workflows.md
version: 1.0.0
status: stable
---

# User Testing Checkpoints

## The Reality: You Are the Tester

The workflow acknowledges that the user (you!) performs all testing. Each subtask implementation includes natural pause points for your testing and feedback.

## Subtask Lifecycle with Testing

```yaml
Complete Subtask Flow:
  1. AI Analysis → "What needs to be done"
  2. Implementation → "Code/changes complete"
  3. Testing Checkpoint → "🧪 Awaiting your test"
  4. User Tests → "You run and evaluate"
  5. Feedback Loop → "Fix issues if found"
  6. Confirmation → "✅ Subtask complete"
```

## Testing Checkpoint Pattern

After implementing each subtask, the AI provides:

```markdown
✅ Implemented: 7.2 Header Component

📋 Ready for Your Testing:
- **Files Changed**: 
  - `/components/Header.tsx` - Main component
  - `/styles/header.module.css` - Styling
  - `/lib/navigation.ts` - Menu logic

- **How to Test**:
  ```bash
  pnpm dev
  # Navigate to http://localhost:3000
  ```

- **What to Check**:
  ✅ Desktop navigation displays correctly
  ✅ Mobile menu hamburger works
  ✅ Theme toggle switches properly
  ✅ Keyboard navigation (Tab through items)
  ✅ Screen reader announces menu state

- **Known Concerns**:
  ⚠️ Mobile menu animation might be too fast
  ⚠️ Focus trap in mobile menu needs verification

I'll pause here for your testing. Let me know:
1. What's working well
2. Any issues you find
3. If you need changes before we continue
```

## Testing Interaction Examples

### Successful Test

```
User: "Tested the header - looks great! The mobile menu works perfectly and keyboard nav is smooth."

AI: "Excellent! Marking 7.2 as complete. Moving to 7.3: Develop Mobile Navigation System.
    
    [Ultrathink: Mobile-first patterns, gesture support needed...]"
```

### Issues Found

```
User: "The theme toggle doesn't persist after page reload, and the mobile menu doesn't close when clicking outside."

AI: "Got it! Let me fix both issues:
    1. Adding localStorage for theme persistence
    2. Implementing click-outside detection for mobile menu
    
    Implementing fixes now..."
```

### Partial Approval

```
User: "The functionality works but the animation feels jarring. Can we make it smoother? Otherwise good to continue."

AI: "I'll note that for polish later and continue with the next subtask. Added to refinements list:
    - [ ] 🎨 Smooth header animations (non-blocking)
    
    Proceeding to 7.3..."
```

## Benefits of Testing Checkpoints

1. **Quality Assurance** - Every subtask is tested before moving forward
2. **User Control** - You decide when implementation meets standards
3. **Rapid Feedback** - Issues caught and fixed immediately
4. **Clear Communication** - Explicit about what needs testing
5. **Progress Visibility** - Testing status tracked in todos and sessions/

## Testing Tips

- **Quick Tests First** - Basic functionality before edge cases
- **Real Devices** - Test on actual phones/tablets when possible
- **Accessibility** - Always check keyboard and screen reader
- **Performance** - Note any lag or slow interactions
- **Edge Cases** - Try unexpected interactions

## Integration with Todo System

```markdown
## Main Task Todo
- [ ] 🎭 Task 7: Core Layout Components (orchestrated)
  - [ ] 7.1: Create Semantic HTML Structure
    - [x] 💻 Implementation complete
    - [x] 🧪 User tested - approved
  - [ ] 7.2: Implement Header Component
    - [x] 💻 Implementation complete
    - [ ] 🧪 Awaiting user testing  ← Current checkpoint
    - [ ] 🔧 Fix any issues
    - [ ] ✅ User approval
  - [ ] 7.3: Develop Mobile Navigation
    - [ ] 💻 Implementation
    - [ ] 🧪 User testing
    - [ ] ✅ Approval
```

## sessions/ Testing Tracking

```markdown
### 📝 Progress Log
- **[HH:MM]** - Starting subtask 7.2: Header Component
- **[HH:MM]** - ✅ Implementation complete, creating testing checkpoint
- **[HH:MM]** - 🧪 TESTING CHECKPOINT: Awaiting user test
  - Files: Header.tsx, header.module.css
  - Focus: Responsive nav, accessibility
- **[HH:MM]** - 👤 User feedback: "Mobile menu overlaps logo on iPhone SE"
- **[HH:MM]** - 🔧 Fixing mobile menu positioning for small screens
- **[HH:MM]** - 🧪 Ready for re-test
- **[HH:MM]** - ✅ User approved: Header component complete
- **[HH:MM]** - Moving to subtask 7.3
```

## Creating Effective Checkpoints

### Include:
- Exact files changed
- Specific test commands
- Clear success criteria
- Known limitations
- Next steps after approval

### Avoid:
- Vague descriptions
- Missing test instructions
- Unclear success criteria
- Hidden assumptions
- Moving forward without confirmation

## Checkpoint Quality Checklist

- [ ] Files listed with full paths
- [ ] Test command provided
- [ ] Success criteria explicit
- [ ] Known issues documented
- [ ] Clear pause for feedback
- [ ] Next step identified

## Remember

**Testing checkpoints are collaboration points.**

They ensure:
- Quality through user validation
- Clear communication of changes
- Immediate feedback loops
- Documented test results
- Controlled progress through tasks