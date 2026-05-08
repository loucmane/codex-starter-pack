# Compaction Protocol Scope Reconciliation

## Context

Task 31 asks for a `CompactionManager`, checkpoint creation before compaction, restoration protocol, incremental checkpoint updates, and history tracking. That wording predates several current systems:

- Task 19 added `python3 scripts/codex-task rollback checkpoint` and `rollback plan` for non-destructive recovery checkpoints.
- Task 42 added safe session continuation and clarified between-session state.
- Task 93 split compaction from session ending and deprecated the old combined `compaction-detection.md` behavior.
- Task 15 made Serena MCP configuration and memory evidence explicit.

The repo therefore does not need a second rollback system or a parallel session manager. It needs a compaction-specific continuation checkpoint that is safe to run while a task remains active.

## Current-State Gap

The active compaction docs still require manual steps:

- update the session;
- write a compaction memory;
- generate a resume message;
- note exact stopping point;
- preserve task/session/plan/work-tracking pointers.

There is no single helper that captures that packet, writes a durable memory file, appends session/tracker evidence, and records checkpoint history. That is the system gap for Task 31.

## Decision

Implement `python3 scripts/codex-task compaction checkpoint` as a continuation checkpoint helper.

The helper is distinct from rollback:

- **Rollback checkpoint**: captures recovery state before risky migration; produces non-destructive recovery guidance; may tag Git.
- **Compaction checkpoint**: captures continuation state before context reset; does not archive, clear symlinks, end the session, tag Git, or produce commit guidance.

## Required Behavior

The helper should:

1. Require an active workflow state:
   - `sessions/current` exists and resolves;
   - `plans/current` exists and resolves;
   - exactly one ACTIVE work-tracking folder exists, or the target folder is specified.
2. Capture a JSON manifest containing:
   - timestamp, task, slug, summary, next step;
   - branch, HEAD, git status;
   - current session, current plan, session state;
   - active work-tracking folder;
   - Taskmaster health snapshot;
   - Serena memory inventory.
3. Render a Markdown resume message suitable for a post-compaction chat.
4. Write a compaction memory under `.serena/memories/compaction_YYYY-MM-DD_task<id>_<slug>.md`.
5. Append checkpoint history to `.plan_state/compaction-history.jsonl`.
6. Log S:W:H:E entries in the active session and tracker.
7. Leave the session active and all current pointers intact.

## Implementation Surfaces

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `templates/workflows/session/compaction.md`
- `templates/behaviors/session/compaction-preparation.md`
- `templates/handlers/triggers/session/prepare-compaction.md`
- Task 31 plan/tracker/work-tracking docs

## Verification Plan

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-task compaction checkpoint --task 31 ...` captured under active reports
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`
