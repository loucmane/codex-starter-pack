# Task 117 Aegis Closeout Gate Kickoff

## Date
2026-05-20

## Context
Task 117 is active on branch `feat/task-117-aegis-closeout-gate` with readiness `READY | task=117` after the guided kickoff flow created the session, plan, and work-tracking scaffold.

## Goal
Implement a portable Aegis closeout gate so installed projects cannot treat agent work as complete until readiness, pending tracking, ordered plan steps, strict verification, evidence cross-references, semantic handoff, and normal git/GitHub guidance checks pass mechanically.

## Key Boundaries
- Keep Taskmaster and Serena optional in portable installed projects.
- Implement closeout in shared Aegis core, not as a Claude-only adapter path.
- Preserve the live-agent workflow proven in Task 116: kickoff, scoped mutation, pending S:W:H:E tracking, `aegis log`, verification, and strict verify.
- Add completion semantics through `aegis closeout` and tests, including installed-target end-to-end and negative cases.
- Do not make `gac` the default; normal git commands are the default when Git work is delegated and auth is available.

## Evidence Roots
- Session: `sessions/2026/05/2026-05-20-002-task117-aegis-closeout-gate.md`
- Plan: `plans/2026-05-20-task117-aegis-closeout-gate.md`
- Work tracking: `docs/ai/work-tracking/active/20260520-task117-aegis-closeout-gate-ACTIVE/`
- Taskmaster task file: `.taskmaster/tasks/task_117.md`
