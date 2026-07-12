# Task 244 Source Closeout Derivation Contract

## Problem

The Aegis source repository intentionally does not install itself and therefore has no
`.aegis/foundation-manifest.json` or `.aegis/state/current-work.json`. After a Taskmaster task
is done and its work-tracking folder is archived, source readiness and `codex-guard` cannot
identify the completed tracker. Keeping a completed folder under `active/` avoids the failure
but misstates lifecycle truth and blocks the next clean kickoff.

## Authority

Completed source state is derivable only when all of these independent facts agree:

1. The checkout has the canonical Aegis source markers.
2. No installed Aegis manifest or current-work state exists.
3. The current branch carries exactly one numeric task identity.
4. Taskmaster contains that task with status `done`.
5. No ACTIVE work-tracking folder exists.
6. Exactly one direct archive child ending in `-COMPLETED` carries the same task identity.
7. The resolved archive stays under the configured archive root.
8. Its `TRACKER.md` exists, references the same task, and declares `**Status**: COMPLETED`.

Missing, ambiguous, or contradictory evidence fails closed. A source archive is a lifecycle
projection, not a replacement for Taskmaster, plans, sessions, trackers, or S:W:H:E history.

## Integration

- `scripts/_source_workflow_state.py` owns source-checkout detection and derivation.
- Source readiness accepts the derived completed tracker, validates current session and plan
  identity, and checks plan/tracker completion parity.
- `scripts/codex-guard` uses the same tracker only when its existing ACTIVE and installed
  current-work paths are unavailable.
- Canonical and packaged readiness/guard assets remain byte-identical. Installed targets do not
  receive the source-only helper, so their current-work behavior is unchanged.
- Existing archive and kickoff helpers remain authoritative; Task 244 does not add another
  lifecycle mutator. In an uninstalled source checkout, archive now rewrites exact ACTIVE-root
  references in the moved Markdown bundle, current plan, and current session, then records fresh
  plan/tracker hashes so the move cannot leave guard evidence pointing at a vanished path.
  Installed targets retain their existing archive behavior.
- `sessions continue` consumes the same derivation when completed source publication crosses a
  date boundary. It creates only the new daily session and progress entries; it does not recreate
  an ACTIVE folder or installed current-work state.

## Fail-Closed Cases

- installed manifest present;
- current-work state present;
- non-Aegis repository;
- branch without a task identity;
- missing or non-done Taskmaster task;
- any ACTIVE folder;
- zero or multiple matching completed archives;
- archive symlink or resolved path outside the archive root;
- missing tracker, mismatched task identity, or non-completed tracker status.

## Dogfood And Rollback

Task 237 is the migration fixture: its complete work-tracking bundle was moved from `active/`
to `archive/` before Task 244 kickoff without deleting evidence or creating installed state.
Task 244 closed by archiving its own completed bundle. The first live guard run found that the
plan still referenced evidence under the moved ACTIVE path. The archive helper was corrected,
the transition was replayed, and source readiness plus guard operation then passed from the
derived archive without installed current-work state.

Rollback restores the previous canonical and packaged readiness/guard assets and retains one
completed tracker under `active/` as the documented compatibility projection. No archive or
historical evidence is deleted during rollback.
