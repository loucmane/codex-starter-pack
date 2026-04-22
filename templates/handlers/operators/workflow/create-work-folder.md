---
id: create-work-folder
name: Create Work Folder
title: Create Work Folder
role: operator
type: operator
domain: workflow
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/workflow/create-work-folder.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
