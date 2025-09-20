---
id: create-work-folder
name: Create Work Folder
role: operator
domain: workflow
stability: stable
triggers: []
dependencies: []
tools:
  - Write
  - Edit
version: 1.0.0
---

#### Handler: create-work-folder {#create-work-folder}
**Triggers**: Automatic from other handlers
**Target Pattern**: Work item name
**Pre-conditions**: 
- No existing folder for work
- Valid work item name
**Process**:
1. Create folder with timestamp
2. Create subfolder structure:
   - plans/ (detailed plans, roadmaps)
   - design/ (DDII documents, analysis, architecture)
   - code/ (code attempts - what worked/failed)
   - archive/ (old versions with .old suffix)
3. Initialize 7 core files (ALL CAPS):
   - IMPLEMENTATION.md (the implementation plan)
   - TRACKER.md (checkbox tasks tracking the plan)
   - CHANGELOG.md (what actually changed/was built)
   - FINDINGS.md (discoveries, test results)
   - DECISIONS.md (key decisions with rationale)
   - MEMORY-REFS.md (related session memories)
   - HANDOFF.md (session transition info)
4. Add initial content with templates
5. Update sessions/
**Success**: 7-file structure with subfolders ready
**Failure**: Folder exists already