---
id: template-system-structure
title: Template System Structure
type: engine-component
status: stable
dependencies: []
exports:
  - registry-structure
  - handlers-structure
  - workflows-structure
  - tools-structure
  - conventions-structure
  - patterns-structure
  - building-better-structure
  - matrices-structure
  - behaviors-structure
---

# Template System Structure

My knowledge lives in these templates that I search dynamically:

## templates/registry - Modular Index
- **Purpose**: Fast lookup of all handlers (modular)
- **When I use it**: FIRST, for every request (prefer Serena MCP)
- **What I find**: Handler names, locations, triggers

## handlers/ - All System Handlers
- **Purpose**: Complete handler collection organized by role and domain
- **Structure**: handlers/triggers/, handlers/orchestrators/, handlers/operators/
- **When I use it**: Loading handlers after finding them in REGISTRY
- **Access methods**: Direct Read for speed, Serena search for flexibility

## templates/workflows/ - Development Processes
- **Purpose**: How to do development work
- **When I use it**: Implementation, features, bugs
- **Key handlers**: start-new-work, fix-problem, test-implementation

## TOOLS.md - Tool Selection
- **Purpose**: Which tool for which task
- **When I use it**: Before any tool operation
- **Key principle**: Serena for search, Edit for files

## templates/conventions/ - Standards & Rules
- **Purpose**: How things should be done
- **When I use it**: Before edits, commits, naming
- **Key rules**: Timestamps, git format, file conventions

## templates/patterns/ - Meta Routing
- **Purpose**: How to route complex requests
- **When I use it**: Ambiguous or multi-step requests
- **Key patterns**: work-activity, tool-selection, evidence-check

## templates/integration/ - Integration
- **Purpose**: How systems connect
- **When I use it**: Cross-system operations
- **Key handlers**: save-context, workflow-to-tool

## templates/matrices/ - Decision Support
- **Purpose**: Quick decision matrices for routing
- **When I use it**: Need fast lookup for common patterns
- **Key matrices**: Request→Handler, File→Convention, Problem→Solution, Context→Mode, Error→Recovery

## BEHAVIORS.md - Automatic Enforcement
- **Purpose**: Behavioral hooks that create "cannot proceed" gates
- **When I use it**: Automatically triggered before actions
- **Key behaviors**: Work tracking, file operations, git conventions, task management

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/structure/template-system.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
