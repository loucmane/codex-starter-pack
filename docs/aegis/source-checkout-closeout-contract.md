# Aegis Source-Checkout Closeout Contract

Status: implemented by Task 244

## Purpose

The Aegis source repository uses Taskmaster, plans, sessions, trackers, and S:W:H:E evidence,
but intentionally does not install itself as a target project. It therefore has no installed
manifest or `.aegis/state/current-work.json` to identify a completed archived tracker.

Task 244 adds a source-only, read-only derivation path. It allows a completed task branch to
archive its work-tracking bundle truthfully and still run readiness and guard checks before the
next task kickoff. It does not remove or replace the legacy workflow surfaces.

## Derivation Requirements

Completed source state exists only when all of these facts agree:

- the checkout contains the canonical Aegis source markers and `pyproject.toml` declares
  `aegis-foundation`;
- no installed Aegis manifest or current-work state exists;
- the branch contains a numeric task ID;
- Taskmaster contains that task with status `done`;
- no ACTIVE work-tracking folder exists;
- exactly one direct `archive/*-COMPLETED` folder matches the task ID;
- the archive is a real in-root directory, not a symlink;
- its tracker is a real file, references the same task, and declares `COMPLETED`;
- the current session and plan reference the same task; and
- required plan and tracker steps are all completed and aligned.

Any missing, ambiguous, or contradictory authority blocks derivation. Installed targets retain
their manifest/current-work contract and never use this fallback.

## Consumers

- `.claude/scripts/readiness.sh` reports terminal source-closeout readiness after validating
  session, plan, and archived tracker parity.
- `scripts/codex-guard` uses the same archived tracker when no ACTIVE or installed current-work
  path exists.
- In the uninstalled source checkout, `scripts/codex-task work-tracking archive` relocates exact
  references to the moved ACTIVE bundle in the archive, current plan, and current session, then
  records fresh plan/tracker hashes. Installed targets retain their existing archive behavior.
  `wizard kickoff` remains the next-task lifecycle mutator.
- The resolver never writes or fabricates installed Aegis state.

## Next-Task Transition

After delivery, archive the completed bundle with the supported helper. In the source checkout,
the helper preserves the whole bundle, rewrites only exact paths made stale by that move, and
refreshes plan-sync evidence. The completed branch can then run readiness and guard from
repository evidence. If publication crosses a date boundary, `sessions continue` reuses the
completed source archive, creates a fresh daily session, and refreshes plan/tracker hashes without
recreating ACTIVE or installed state. A new task uses the normal task-bearing branch and guided
kickoff, which creates a fresh ACTIVE tracker and restores ordinary in-progress readiness.

## Rollback

Revert the Task 244 resolver and its readiness/guard integrations, then retain one completed
tracker under `active/` as the previous compatibility projection. Do not delete the archived
bundle, plans, sessions, handoffs, or S:W:H:E evidence.
