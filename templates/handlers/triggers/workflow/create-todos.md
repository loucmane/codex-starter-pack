---
id: create-todos
name: Create Todos
role: trigger
domain: workflow
stability: stable
triggers:
  - "plan out X"
  - "break down Y"
  - "create tasks for Z"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---

#### Handler: create-todos {#create-todos}
**Triggers**: "plan out X", "break down Y", "create tasks for Z"
**Target Pattern**: Work item to decompose
**Pre-conditions**: 
- Clear understanding of overall goal
- TodoWrite tool available
**Process**:
1. Analyze work scope
2. Break into logical phases
3. Create hierarchical task structure
4. Set appropriate priorities
5. Add to TodoWrite
6. Show task breakdown to user
**Success**: Comprehensive task list created
**Failure**: Scope unclear, needs discussion
**Examples**:
- "plan out the migration" → Detailed migration steps
- "break down the feature" → Implementation tasks