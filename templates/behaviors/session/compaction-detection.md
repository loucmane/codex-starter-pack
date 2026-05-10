---
trigger: DEPRECATED - See templates/behaviors/session/session-end.md and templates/behaviors/session/compaction-preparation.md
title: Session Compaction Detection [DEPRECATED]
action: Redirect to the active session-end and compaction-preparation behaviors
blocks: Do not use this file as executable workflow guidance
category: session
type: behavior
enforcement: deprecated
status: deprecated
version: 3.0.0
deprecated_since: 2026-04-23
replacement: templates/behaviors/session/templates/behaviors/session/compaction-preparation.md
migration_notice: Use compaction-preparation for context-limit checkpoints and session-end for actual session closure.
---

# Session Compaction Detection [DEPRECATED]

> This file remains only as a compatibility tombstone for older references.
>
> Use these active sources instead:
> - **[templates/behaviors/session/compaction-preparation.md](compaction-preparation.md)** for context-limit checkpoints and resume instructions.
> - **[templates/behaviors/session/session-end.md](session-end.md)** for actual session closure, handoff, and commit guidance.

## Why This File Exists

Older docs and memories referred to a combined "compaction detection" behavior. That combined flow caused repeated confusion because it mixed two distinct operations:

1. **Compaction**: save state, keep the session active, and provide resume instructions.
2. **Session end**: close the session/task work, update handoff state, and provide commit guidance.

Task 93 retires this file as executable behavior so the repo has one canonical source for each workflow.

## Migration Rule

- If the trigger is about context limits, capacity, or opening a new chat, follow `templates/behaviors/session/compaction-preparation.md`.
- If the trigger is about stopping work, wrapping up for the day, or final handoff, follow `templates/behaviors/session/session-end.md`.
- Do not treat compaction as implicit session ending.
- Do not generate commit guidance from compaction-only prompts.

## Canonical Sources

- Compaction behavior: [templates/behaviors/session/compaction-preparation.md](compaction-preparation.md)
- Session ending behavior: [templates/behaviors/session/session-end.md](session-end.md)
- Compaction trigger handler: [../../handlers/triggers/session/prepare-compaction.md](../../handlers/triggers/session/prepare-compaction.md)
- Session compaction workflow: [../../workflows/session/compaction.md](../../workflows/session/compaction.md)

## Compatibility Note

If another document still links here, update that document to point directly to the relevant active source instead of reintroducing combined guidance in this file.

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/session/compaction-detection.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
