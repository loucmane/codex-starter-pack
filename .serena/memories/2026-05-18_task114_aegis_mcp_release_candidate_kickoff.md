# 2026-05-18 Task 114 Aegis MCP Release Candidate Kickoff

## Context
- Task: 114 - Aegis MCP Release Candidate Validation.
- Branch: feat/task-114-aegis-mcp-release-candidate.
- Active work-tracking: docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/.
- Session: sessions/2026/05/2026-05-18-002-task114-aegis-mcp-release-candidate.md.
- Plan: plans/2026-05-18-task114-aegis-mcp-release-candidate.md.

## Scope
Task 114 validates whether the packaged Aegis CLI and MCP server can be treated as a release candidate from clean external projects. Evidence must prove installed-artifact behavior, not just source-checkout behavior.

## Current State
- Parent Task 114 is in progress.
- Subtask 114.1 is done after adding the release-candidate contract and test matrix.
- Subtask 114.2 is in progress for building and inspecting release-candidate wheel/sdist artifacts.
- Provisional release-channel decision: validate local wheel/sdist artifacts first, treat GitHub release artifacts as likely first public channel if RC evidence is green, and defer PyPI to a later explicit task.

## Resume
Start with subtask 114.2: build wheel/sdist, inspect metadata/package data/entry points, and store evidence under reports/aegis-mcp-release-candidate/.
