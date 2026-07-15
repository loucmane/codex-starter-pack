# Task 257: Canonical Codex Home Cutover Plan

Status: **Proposed; Task 256 plan output only**

Execution authority: **none in Task 256**

Expected Taskmaster task: **257 — Perform the attended drain-first canonical Codex home cutover**

Binding architecture: [Canonical Codex Home Architecture](canonical-codex-home-architecture.md)

## Outcome

Task 257 will replace the current split Codex topology with:

- one official Codex executable identity;
- one canonical `CODEX_HOME`;
- one canonical `CODEX_SQLITE_HOME`;
- one native Remote Control app server owned by those homes;
- one session inventory;
- project-local trust, configuration, and hooks loaded through native Codex behavior; and
- one client-local exact-definition hook trust store reviewed through `/hooks`.

The expected canonical `CODEX_HOME` on this host is `/home/loucmane/.codex`. Task 257 must
revalidate that choice before mutation. The current transition candidate is
`/home/loucmane/codex/.codex/remote-control`. Neither value authorizes a cutover by itself.

Task 257 does not copy or merge live state indiscriminately. It drains work, identifies the owner
of every state surface, records an explicit disposition for non-canonical state, preserves exact
rollback material, and then changes one authority boundary at a time.

## Current-host facts to revalidate

Task 256 observed these facts read-only. They are volatile and must be re-collected in Task 257:

- the ordinary and isolated Remote Control homes both own session files;
- more than one app-server control socket exists;
- command candidates resolve to more than one executable identity;
- `/home/loucmane/.local/bin/codex-wrapper` contains context-sensitive `CODEX_HOME` routing;
- the ordinary home contains SQLite state under more than one candidate root;
- the isolated home did not expose a separate `state_*.sqlite` file in the bounded scan;
- a sandboxed process namespace could not prove host-wide process completeness; and
- active child work was not proven drained.

These observations diagnose the migration problem. They do not authorize a lifecycle action or
identify the active SQLite database.

## Non-negotiable safety rules

Task 257 must never:

- use `kill`, `pkill`, signals, or process termination as a lifecycle fallback;
- stop a server whose owning home, socket, PID, version, and native supervisor are not all proven;
- copy a live SQLite database, WAL, or shared-memory file;
- copy or merge authentication, connector credentials, project trust, or hook-trust hashes;
- synthesize Codex session rows or modify a session database directly;
- claim hooks are trusted because tracked guidance or hash records exist;
- use `--dangerously-bypass-hook-trust`;
- reset, clean, stash, rebase, or switch the Blog Task 41 checkout;
- begin Taskmaster-to-Gas-Town migration;
- delete either original Codex home during the cutover; or
- retire the wrapper or Task 255 bridge before the observation window succeeds.

Every mutation must have a byte-, mode-, owner-, and symlink-aware rollback record created before
that mutation. A failed verification stops the run and invokes the phase-local rollback; it never
causes the plan to skip ahead.

## Task 257 task contract

Create Task 257 only after Task 256 is merged. The task description must include:

1. the binding ADR and this runbook;
2. the exact canonical and candidate home paths;
3. all active thread IDs and project paths that need preservation dispositions;
4. a prohibition on Blog product or Task 41 mutation;
5. an attended boundary before the first host mutation;
6. an attended `/hooks` boundary after the fresh Blog session displays exact definitions;
7. a requirement to preserve both original homes through the observation window; and
8. a final report comparing pre-cutover and post-cutover topology facts.

Task 257 should use a task-bearing upstream Aegis branch for evidence and implementation notes.
Host snapshots must be stored in a private, owner-approved location outside both live Codex homes;
they must not be committed if they reveal host identities or sensitive metadata.

## Phase 257.0 — Read-only preflight and authority freeze

### Preconditions

- Task 256 is merged and installed from its stable source commit.
- The upstream Aegis source checkout and Blog checkout are at known, safe checkpoints.
- The owner identifies every active ordinary, Remote Control, TUI, automation, and child-agent run.
- No host mutation has begun.

### Diagnostic command shape

Run from a host-complete attended shell, not from a sandboxed PID namespace:

```bash
aegis codex topology status \
  --canonical-codex-home /home/loucmane/.codex \
  --candidate-codex-home /home/loucmane/codex/.codex/remote-control \
  --project /home/loucmane/codex \
  --project /home/loucmane/dev/blog \
  --codex-command /home/loucmane/.local/bin/codex-wrapper \
  --codex-command /home/loucmane/.local/bin/codex \
  --codex-command /home/loucmane/.codex/packages/standalone/current/bin/codex \
  --codex-command /home/loucmane/codex/.codex/remote-control/packages/standalone/current/bin/codex \
  --process-scope host \
  --active-work-state unknown \
  --json
```

Add every relevant thread with repeatable `--thread` arguments and every observed launcher,
wrapper, and official package binary with repeatable `--codex-command` arguments. Do not declare
`--active-work-state drained` until two independent checks prove it. Do not specify
`--canonical-sqlite-home` until the active SQLite authority is proven.

Then render the same no-mutation plan:

```bash
aegis codex topology plan \
  --canonical-codex-home /home/loucmane/.codex \
  --candidate-codex-home /home/loucmane/codex/.codex/remote-control \
  --project /home/loucmane/codex \
  --project /home/loucmane/dev/blog \
  --codex-command /home/loucmane/.local/bin/codex-wrapper \
  --codex-command /home/loucmane/.local/bin/codex \
  --codex-command /home/loucmane/.codex/packages/standalone/current/bin/codex \
  --codex-command /home/loucmane/codex/.codex/remote-control/packages/standalone/current/bin/codex \
  --process-scope host \
  --active-work-state unknown \
  --json
```

### Required determinations

- Which official binary and version will be canonical?
- Which exact config sets the effective `CODEX_SQLITE_HOME`?
- Which `state_*.sqlite` file is open by the canonical server, if any?
- Which home owns each live server, daemon loop, client, and requested thread?
- Which control socket belongs to which proven server?
- Which sessions exist only in the non-canonical home?
- Which work is active, queued, resumable, or safe to hand off?
- Which projects require a fresh post-trust session?

### Stop conditions

Stop before mutation if process scope is unknown, any server owner is unknown, session ownership is
ambiguous, config is malformed, SQLite authority is ambiguous, or active work is present or
unknown.

## Phase 257.1 — Exact rollback inventory

After preflight is unambiguous, snapshot only the metadata and files needed for exact rollback:

- effective executable paths, versions, file digests, modes, owners, and symlink targets;
- canonical and candidate home paths and directory ownership;
- config files, preserving marker-external bytes and mode `0600` where applicable;
- shell and launcher files that Task 257 proposes to change;
- wrapper path, digest, mode, and symlink identity;
- server PIDs, parent PIDs, native supervisor metadata, and Unix socket identities;
- SQLite paths and open-file ownership, without copying a live database;
- session inventories by ID and owning home, without reading transcript text into evidence; and
- tracked project hook-definition digests, without reading or copying the client trust store.

The rollback packet must map each planned mutation to its exact restore source and verification
command. It must be readable before Phase 257.2. If secrets would be captured, redesign the
snapshot rather than weakening storage controls.

Attended boundary A: the owner reviews the topology report, the selected canonical executable and
SQLite home, every non-canonical state disposition, and the rollback packet before drain begins.

## Phase 257.2 — Drain and preserve active work

### Drain protocol

1. Stop new autonomous dispatch through its supported project-level control; do not alter hook
   trust.
2. Let active tool calls, PR delivery, and child agents finish.
3. For each thread in the non-canonical home, choose exactly one disposition:
   - already represented by merged Git/evidence and safe to archive;
   - resumable in the canonical home through an official same-home mechanism after cutover;
   - preserved as an Aegis capsule/handoff for a fresh canonical session; or
   - retained read-only in the quarantined legacy home for later attended recovery.
4. Do not fabricate a cross-home native resume. If Codex has no supported import, use a capsule or
   retain the source home.
5. Re-run host-complete process and thread diagnostics.
6. Obtain an independent second confirmation that no child work remains.

Only after those checks may the status command use `--active-work-state drained`.

Attended boundary B: the owner confirms the drain report and explicitly authorizes the first live
host mutation.

## Phase 257.3 — Stop only the proven legacy server

Use native lifecycle control in an explicit legacy owner context. Before invocation, print and
review:

- selected `CODEX_HOME` and `CODEX_SQLITE_HOME`;
- exact native Codex executable and version;
- target control socket;
- server PID and parent/supervisor PID;
- active-child count; and
- the canonical server identity that must remain untouched.

Invoke only native `codex remote-control stop` through that proven context. A wrong-home,
unmanaged-server, version, socket, or ownership mismatch is a hard stop. Never fall back to a
signal.

Verify that the exact legacy PID and socket disappeared, the canonical context stayed unchanged,
and no unrelated global or WSL server was affected.

Rollback: restart only the exact previous legacy server through its proven native executable and
home. If that ownership cannot be reproduced, stop and restore routing snapshots before doing
anything else.

## Phase 257.4 — Consolidate durable authority

This phase runs only while the legacy server is stopped and canonical SQLite ownership is
quiescent.

### Canonical configuration

- preserve `/home/loucmane/.codex` as the expected canonical owner unless preflight disproves it;
- set one explicit effective `CODEX_SQLITE_HOME` only after open-file evidence identifies the
  intended database;
- preserve canonical authentication, connectors, skills, package metadata, project trust, and
  hook trust in place; and
- do not replace canonical config with the isolated-home config wholesale.

### Non-canonical sessions

Use only an officially supported import/handoff if one exists and has been tested on snapshots.
Otherwise, preserve fresh-session capsules and keep the original session files read-only in the
quarantined legacy home. Never write synthetic rows to SQLite or copy a session database.

### Trust

Project trust may be reconstructed through normal trusted-project configuration, but client hook
approval is not migrated. Never copy hashes between homes. The canonical client must perform its
own attended `/hooks` review later.

Verification before routing changes:

- canonical config parses;
- marker-external bytes and protected modes are unchanged;
- one selected SQLite authority is documented and quiescent;
- no duplicate active auth, trust, or SQLite authority was created; and
- every non-canonical session has its approved disposition.

Rollback: restore exact snapshots while all affected servers remain stopped. Do not start a server
against partially restored state.

## Phase 257.5 — Replace split routing with one canonical environment

Only now may Task 257 change shell or launcher configuration. The final route must use:

- one official Codex executable;
- `CODEX_HOME=/home/loucmane/.codex` unless preflight selected another owner;
- the proven canonical `CODEX_SQLITE_HOME`; and
- native Remote Control commands without CWD-based home selection.

Do not delete the wrapper. First remove its authority from the active route or change it to a
transparent, context-independent invocation. Preserve its exact previous bytes for rollback. Do
not modify project files to compensate for host routing.

Open a fresh shell and verify `command -v`, resolved executable identity, version, `CODEX_HOME`,
`CODEX_SQLITE_HOME`, and topology from the Aegis source directory, Blog, and an unrelated ordinary
project. Every location must resolve to the same host context.

Rollback: restore exact shell, PATH, symlink, and wrapper snapshots. This rollback must not touch
sessions, auth, project trust, or hook trust.

## Phase 257.6 — Start one canonical native server

Run native `codex remote-control start` exactly once in the newly verified canonical context.
Do not use a retained compatibility client, hard-coded socket, startup-update suppression, or
installed-version symlink mutation as part of the steady state.

Verify:

- exactly one intended native Remote Control server and one control socket exist;
- its executable, version, home, SQLite owner, parent, and socket match the plan;
- lifecycle `status`, `start`, and `stop` target that same context;
- unrelated global or WSL processes remain unaffected; and
- the topology report no longer detects dual server or executable authority.

Rollback: stop this server through the same proven native context, restore routing and durable
state snapshots, and only then restart the old server if the rollback plan requires it.

## Phase 257.7 — Fresh project sessions and attended hook review

Create a new Blog session from `/home/loucmane/dev/blog`; do not resume the pre-trust thread. The
new session must load project-local `.codex/` configuration from the canonical home context.

Run `/hooks` and stop for owner review of the exact definitions and hashes. The expected Blog hash
recorded during the earlier rollout was
`3334c040bd46a92bd542d53e2919a43b14ba1bf001fa79883a5385dc5ba487d5`, but Task 257 must compute
and review the current exact definition rather than trusting this historical value.

Do not auto-approve, copy trust, or bypass review. After attended approval, start a second fresh
Blog session. Only a post-approval hook event from that second SessionStart can support a claim
that hooks executed. Approval alone is not execution evidence.

The Blog Task 41 working tree must remain byte-for-byte untouched unless its owner separately
authorizes a managed project update after the host cutover.

Attended boundary C: exact-definition `/hooks` review and approval.

## Phase 257.8 — System canaries

Run canaries from the canonical environment:

1. `aegis codex topology status` reports one home, one SQLite authority, one executable identity,
   one native server, and no unresolved ownership issue.
2. Native same-home resume and fork can see expected canonical sessions.
3. A cross-home historical ID receives an honest ownership/handoff diagnosis, not an empty picker
   presented as absence.
4. Ordinary CLI use and Remote Control use share the canonical state inventory.
5. A fresh trusted project loads project-local config.
6. A changed hook definition requires renewed `/hooks` review.
7. Aegis strict verification passes in Aegis and in a safe project checkpoint.
8. Existing project CI, evidence-gated delivery, and Remote Control smoke tests pass.
9. No project required copied credentials, sessions, trust records, or hook hashes.

If a state-integrity canary fails, stop the canonical server natively and execute the full rollback.
If one project-only canary fails, preserve the canonical host and roll back that project separately.

## Phase 257.9 — Observation and quarantine

Quarantine the old isolated home and wrapper route without deleting either. Make accidental use
visible and reversible. Observe at least:

- ordinary sessions;
- Remote Control sessions;
- resume and fork;
- compaction and continuation;
- project trust changes;
- hook-definition changes and renewed review;
- autonomous delivery; and
- a clean shell/login restart.

No access to the quarantined home should occur during the observation window. Keep rollback
artifacts intact. Wrapper retirement, bridge retirement, and legacy-home deletion require a later
reviewed cleanup task after the window passes; they are not Task 257 success criteria.

## Completion evidence

Task 257 is complete only when its report contains:

- the final canonical executable, version, `CODEX_HOME`, and `CODEX_SQLITE_HOME`;
- pre- and post-cutover topology reports;
- server PID/socket/home ownership before and after;
- a disposition for every non-canonical thread and state store;
- the three attended approvals and exact boundaries they authorized;
- evidence that the Blog definition was reviewed through `/hooks` without copied trust;
- evidence from a second fresh SessionStart;
- all canary and strict-verification results;
- a rollback drill or mechanically verified rollback packet;
- confirmation that Blog Task 41 and unrelated project work were untouched; and
- the observation-window owner and end condition.

## Success definition

The cutover succeeds when a project path no longer selects a Codex home indirectly: ordinary and
Remote Control sessions use one native context, resume/fork use one inventory, lifecycle commands
target one proven owner, trusted project configuration loads in fresh sessions, and hook approval
remains an attended exact-definition client boundary.

Fewer wrappers are not the primary outcome. One coherent ownership model is.
