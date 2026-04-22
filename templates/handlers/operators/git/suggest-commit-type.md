---
id: suggest-commit-type
name: Suggest Commit Type
title: Suggest Commit Type
role: operator
type: operator
domain: git
stability: stable
status: stable
triggers:
  - "what type is this change"
  - "commit type for X"
  - "should this be feat or fix"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: suggest-commit-type {#suggest-commit-type}
**Triggers**: "what type is this change", "commit type for X", "should this be feat or fix"
**Target Pattern**: Change description
**Pre-conditions**: 
- Changes understood
- Commit types defined
**Process**:
1. Analyze change nature
2. **PRIMARY**: Match to types:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation
   - style: Formatting
   - refactor: Code restructure
   - test: Test changes
   - chore: Maintenance
3. Consider impact
4. Recommend type with reasoning
**Success**: Clear type recommendation
**Failure**: Ambiguous change type
**Examples**:
- "added login button" → feat
- "fixed typo in readme" → docs

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/git/suggest-commit-type.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
