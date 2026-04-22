---
id: create-component
name: Create Component
title: Create Component
role: trigger
type: trigger
domain: development
stability: stable
status: stable
triggers:
  - "create a new component"
  - "build component X"
  - "new component for Y"
dependencies: []
tools:
  - Write
  - Edit
version: 1.0.0
---

#### Handler: create-component {#create-component}  
**Triggers**: "create a new component", "build component X", "new component for Y"
**Target Pattern**: Component name and type
**Pre-conditions**: 
- Component doesn't already exist
- Valid component location identified
**Process**:
1. Check existing component patterns
2. Determine component type (UI, logic, hybrid)
3. Create component file(s)
4. Add necessary imports/exports
5. Create basic tests
6. Update component index if exists
**Success**: Component created following patterns
**Failure**: Component exists, suggest alternative
**Examples**:
- "create a Button component" → UI component with styles
- "new auth provider component" → Context/provider pattern

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/development/create-component.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
