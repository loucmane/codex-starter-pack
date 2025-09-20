---
title: Behavioral Hooks System
description: Automatic behavioral hooks that enforce conventions and guide actions
type: index
version: 1.0.0
---

# Behavioral Hooks System

This directory contains all automatic behavioral hooks that enforce conventions and guide actions. These are the "cannot proceed without" gates that make the system work naturally.

## 🎯 System Overview

Behavioral hooks create mandatory checkpoints that ensure proper execution. Each behavior:
- **Triggers** on specific conditions
- **Blocks** progress until satisfied
- **Enforces** conventions automatically
- **Maintains** system integrity

## 📂 Behavior Categories

### [file-operations/](file-operations/)
Behaviors that trigger before file modifications:
- [before-edit.md](file-operations/before-edit.md) - Convention checks before editing
- [before-create.md](file-operations/before-create.md) - Validation before creating files

### [timestamps/](timestamps/)
Time-related enforcement:
- [before-adding.md](timestamps/before-adding.md) - Actual time verification

### [git/](git/)
Version control behaviors:
- [before-commit.md](git/before-commit.md) - Commit format and gac validation

### [work-tracking/](work-tracking/)
Documentation enforcement:
- [update-tracker.md](work-tracking/update-tracker.md) - Progress tracking requirements

### [validation/](validation/)
Evidence and verification:
- [evidence-claims.md](validation/evidence-claims.md) - Proof before assertions

### [task-management/](task-management/)
Task and todo behaviors:
- [todo-write.md](task-management/todo-write.md) - Task list enforcement

### [session/](session/)
Session lifecycle management:
- [session-end.md](session/session-end.md) - Proper session closure with status
- [compaction-preparation.md](session/compaction-preparation.md) - Context limit handling
- ~~[compaction-detection.md](session/compaction-detection.md)~~ - DEPRECATED (split into above)

## 🔗 Integration Points

### ULTRATHINK Enforcement
The core ULTRATHINK enforcement pattern is maintained in:
- [templates/shared/patterns/ultrathink-format.md](../templates/shared/patterns/ultrathink-format.md)

This pattern is referenced by all behaviors that require development context.

### Cross-Template References
- **CLAUDE.md** → Invokes these behaviors as execution gates
- **WORKFLOWS.md** → References for work tracking enforcement
- **CONVENTIONS.md** → Automated through these behaviors
- **REGISTRY.md** → Lists all behaviors with locations
- **MATRICES.md** → Error recovery behaviors

## 🚀 Quick Navigation

| Behavior | Trigger | Purpose |
|----------|---------|---------|
| [File Edit Check](file-operations/before-edit.md) | Before Edit/MultiEdit | Enforce file conventions |
| [File Creation Guard](file-operations/before-create.md) | Before Write new file | Prefer editing over creating |
| [Timestamp Accuracy](timestamps/before-adding.md) | Adding any timestamp | Use actual system time |
| [Commit Format](git/before-commit.md) | User says "gac" | Validate commit format |
| [Work Updates](work-tracking/update-tracker.md) | Progress milestones | Keep tracking current |
| [Evidence Required](validation/evidence-claims.md) | Making code claims | Proof before assertions |
| [Todo Enforcement](task-management/todo-write.md) | Starting work | Task list required |
| [Session End](session/session-end.md) | End signals | Proper session closure |
| [Compaction Prep](session/compaction-preparation.md) | Memory limits | Context checkpoint |

## ⚡ Enforcement Strength

All behaviors maintain "cannot proceed without" enforcement:
- **BLOCKS**: Hard stop until satisfied
- **MANDATORY**: Not optional or skippable
- **AUTOMATIC**: Triggered by context
- **NATURAL**: Becomes part of workflow

## 🔧 Adding New Behaviors

When adding a new behavior:
1. Create file in appropriate category folder
2. Include YAML frontmatter with:
   - `trigger`: What activates the behavior
   - `action`: What must happen
   - `blocks`: What's prevented until satisfied
3. Define clear satisfaction criteria
4. Add cross-references to related behaviors
5. Update this index with the new behavior
6. Add to REGISTRY.md if significant

## 📝 Behavior Template

```yaml
---
trigger: [What activates this behavior]
action: [What must be done]
blocks: [What cannot proceed without this]
category: [file-operations|timestamps|git|work-tracking|validation|task-management|session]
enforcement: mandatory
version: 1.0.0
---

# Behavior Name

## Trigger Condition
[Detailed description of when this fires]

## Required Action
[Step-by-step what must happen]

## Blocking Gate
[What specifically is prevented until satisfied]

## Satisfaction Criteria
[How to know the behavior is complete]

## Cross-References
- Related behaviors
- Template references
- Convention links
```

## 🎯 Remember

Behaviors are not suggestions - they are mandatory execution gates that ensure system integrity. Every behavior here becomes an interrupt in the execution flow, ensuring conventions are followed naturally and automatically.