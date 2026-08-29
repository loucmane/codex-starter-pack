# Aegis Source-Checkout Closeout Contract

Status: bead-native completion implemented; transactional lifecycle implemented by `ga-ejrm`

## Purpose

The Aegis source repository uses a Gas City bead as its work authority plus plans, sessions,
trackers, and S:W:H:E evidence, but intentionally does not install itself as a target project.
It therefore has no installed manifest or `.aegis/state/current-work.json` to identify a
completed archived tracker. Historical Taskmaster closeouts remain readable compatibility
evidence; new work is bead-native.

The source-only resolver allows a completed bead branch to archive its work-tracking bundle
truthfully and still run readiness and guard checks before the next kickoff. The lifecycle is
derived as one of three states:

- `ACTIVE`: exactly one current plan, session, and ACTIVE tracker agree on one work identity;
- `IDLE`: no ACTIVE tracker exists and the current plan/session resolve to one verified
  completed archive (or the repository has not begun its first session); or
- `CLOSEOUT_PENDING`: the write-ahead closeout journal exists and must be reconciled before
  kickoff or persistent mutation.

Readiness and lifecycle are deliberately separate. `IDLE` describes the workflow lifecycle;
readiness may still be `BLOCKED` on a new bead branch until kickoff creates its ACTIVE envelope.

## Derivation Requirements

Completed source state exists only when all of these facts agree:

- the checkout contains the canonical Aegis source markers and `pyproject.toml` declares
  `aegis-foundation`;
- no installed Aegis manifest or current-work state exists;
- the branch, or the current plan/session pointers on the default branch, identifies one bead or
  one historical Taskmaster task;
- for historical Taskmaster work, Taskmaster contains that task with status `done`;
- no ACTIVE work-tracking folder exists;
- exactly one direct `archive/*-COMPLETED` folder matches the work ID;
- the archive is a real in-root directory, not a symlink;
- its tracker is a real file, references the same work ID, and declares `COMPLETED`;
- the current session and plan reference the same work ID; and
- required plan and tracker steps are all completed and aligned.

Any missing, ambiguous, or contradictory authority blocks derivation. Installed targets retain
their manifest/current-work contract and never use this fallback.

## Consumers

- `aegis gate readiness` reports `ACTIVE`, `IDLE`, or `CLOSEOUT_PENDING` alongside its
  authorization result after validating session, plan, and tracker parity.
- `scripts/codex-guard` uses the same archived tracker when no ACTIVE or installed current-work
  path exists.
- In the uninstalled source checkout, `scripts/codex-task work-tracking archive` creates a
  write-ahead journal before the first bundle mutation, annotates the bundle idempotently, moves
  it atomically, rewrites only exact stale references, and records fresh plan/tracker hashes.
  The journal is deleted only after terminal verification succeeds.
- `scripts/codex-task work-tracking reconcile` resumes the exact journaled transaction after an
  interruption. Repeating archive after successful closeout is a verified no-op.
- `wizard kickoff` remains the next-work lifecycle mutator and refuses while closeout is pending.
- Installed targets retain their existing archive behavior and do not use the source journal.
- The resolver never writes or fabricates installed Aegis state.

## Next-Task Transition

After delivery, archive the completed bundle with the supported helper. If a process exits at any
phase, readiness blocks as `CLOSEOUT_PENDING`; run the supported reconcile command rather than
editing paths or logs by hand. The completed branch then reports `IDLE` and can run readiness and
guard from repository evidence. If publication crosses a date boundary, `sessions continue`
reuses the completed source archive, creates a fresh daily session, and refreshes plan/tracker
hashes without recreating ACTIVE or installed state. A new bead uses its `codex/<bead>-<slug>`
branch and guided kickoff, which creates a fresh ACTIVE tracker and restores in-progress
readiness.

## Rollback

Revert the lifecycle resolver and transactional archive integration together. If a journal exists,
finish or roll back that exact transaction before reverting; never delete a pending journal as a
shortcut. Do not delete the archived bundle, plans, sessions, handoffs, or S:W:H:E evidence.
