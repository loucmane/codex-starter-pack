# Task 96 Wizard Flow Design

## Purpose

Turn the older interactive-wizard draft into a concrete first implementation that fits the current repository. The repo already has reliable helpers for work-tracking, plan sync, and session logging, so the wizard should orchestrate those helpers rather than replace them.

## Scope Decision

Task 96 implements:

- `python3 scripts/codex-task wizard kickoff`

This kickoff flow is intentionally narrow. It should:

1. confirm or collect task metadata
2. scaffold the active work-tracking folder
3. create a compliant session file
4. create a compliant plan file
5. repoint `sessions/current`, `plans/current`, and `sessions/state.json`
6. mark the Taskmaster task `in-progress`
7. seed the initial plan sync entry

## Why This Slice

- It removes the most repetitive manual setup work.
- It uses the existing helper and guard system instead of bypassing it.
- It is deterministic enough to test.
- It leaves room for richer interactive flows later without overcommitting the design now.

## Enforcement Boundary

The kickoff wizard should enforce:

- feature branch prefix must match the target task ID
- no second active folder unless explicitly forced
- generated plan/tracker parity is immediately synced
- session state points at the newly created session

The kickoff wizard should not try to:

- replace Serena memory capture
- make free-form implementation decisions
- run the full guard after kickoff before same-day findings/decisions/changelog entries exist
- model multi-template workflows yet

## Future Extensions

Possible follow-ons after Task 96:

- resume/continuation wizard
- guided documentation updates using presets
- richer prompt menus for domain-specific task types
- integration with future metrics/dashboard telemetry in Task 97
