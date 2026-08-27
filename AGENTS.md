# Gas City Beads — Agent Integration Guide

## Workflow Authority

Gas City beads are the authoritative work ledger for new work in this repository.
Do not create a parallel Taskmaster task for the same work.

- A bead records the task, status, dependencies, evidence, and outcome.
- A bead must live in the same rig store as the agent that will work it.
- Creating or updating a bead does not authorize routing, resuming a rig, spawning a
  worker, merging, deploying, or changing live infrastructure.
- Use supported `gc bd`/`bd` APIs. Raw SQL is an exceptional, separately authorized
  recovery path only after supported APIs are proven unable to reach the state.

The default local city and primary implementation rig are:

```text
city: /home/loucmane/gascity/city
rig:  gascity
gc:   /home/loucmane/gascity/bin/gc
```

Always pass the city and rig explicitly when operating outside the rig directory.
This prevents cross-store reads and accidental creation in another configured repo.

## Essential Commands

Use the deterministic operator PATH when commands must reach the managed `gc`, `bd`,
and `dolt` binaries:

```bash
/usr/bin/env PATH=/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin \
  /home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city \
  --rig gascity bd ready
```

### Find and inspect work

```bash
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd ready
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd list
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd show ga-xxxx
```

### Create work

```bash
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity \
  bd create "Short outcome-oriented title" \
  --type task --priority P2 \
  --description "Problem, scope, and constraints." \
  --acceptance "Observable completion criteria." \
  --labels "area,workflow"
```

After creation, read the bead back from the same explicitly selected rig store.

### Claim and update work

```bash
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd update ga-xxxx --claim
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd update ga-xxxx --status in_progress
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd update ga-xxxx --append-notes "Evidence-backed progress note."
```

### Dependencies

Use the supported dependency API and verify both directions after mutation:

```bash
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd dep add ga-child ga-parent
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd show ga-child --json
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity bd show ga-parent --json
```

Do not infer dependency direction from prose. Use a dry run when the surface offers one,
then read back the resulting graph.

### Close work

```bash
/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city --rig gascity \
  bd close ga-xxxx --reason "Completed and verified: <concise evidence>."
```

Close only after the acceptance criteria are actually satisfied. A failed canary or
implementation attempt is closed honestly with its failure classification and preserved
evidence; do not erase or reuse it as a later success. Continue with a fresh append-forward
bead when a clean retry is required.

## Daily Workflow

1. Identify the correct city and rig.
2. Inspect `bd ready`, then `bd show <id>` including dependencies and acceptance criteria.
3. Confirm the requested action is authorized independently of bead status.
4. Claim or mark the bead `in_progress` only when work actually begins.
5. Work on a `codex/<bead-id>-<slug>` branch or an explicitly authorized branch.
6. Add concise evidence-bearing notes at meaningful checkpoints.
7. Run focused tests and proportional regression checks.
8. Read back the bead, Git state, and any live state changed.
9. Close PASS or FAIL honestly; never convert failure evidence into a success record.

## Routing and Lifecycle Are Separate Gates

Ledger operations are not dispatch authority.

- `gc sling` routes work and may create demand; do not run it merely because a bead exists.
- `gc rig resume`, `gc resume`, `gc start`, and restarts are lifecycle mutations and require
  their own authority.
- Prefer `--no-formula --no-convoy` only when a reviewed direct-route package explicitly
  requires it; it is not a universal default.
- A route, resume, worker spawn, signing operation, push, merge, install, restart, or
  deployment must stay within the operator's stated scope.

## Store and Command Safety

- Treat bead IDs as store-scoped. Verify the ID resolves from the intended rig before update.
- New creates require an explicitly selected rig. Never rely on contributor auto-routing.
- In classifier/allowlist-sensitive commands, type actual runtime IDs and paths as literal
  characters. Shell variables, substitutions, wrappers, and `env` prefixes can change policy
  matching and execution context.
- Prefer absolute managed binaries under `/home/loucmane/gascity/bin`.
- Preserve before/after JSON for sensitive metadata, dependency, routing, and close mutations.
- Stop on store mismatch, identity drift, unexpected materialization, or partial mutation.

## Codex and Reviewer Roles

- Codex is the executing/orchestrating lane unless the user says otherwise.
- A designated reviewer such as Fable remains read-only: verify claims, identify missing
  gates, and return a verdict. Review does not grant execution authority.
- Executor briefs name the bead ID, rig, objective, acceptance criteria, branch/worktree,
  allowed write scope, tests, and stop conditions.
- Checker reports use the bead ID—not a Taskmaster ID—as the work identity.

## Evidence and Repository Workflow

This repository still uses Aegis session/plan/work-tracking evidence for source changes.
That audit trail complements the bead; it does not replace or duplicate the work ledger.

- Use native file/edit/test/Git tools for implementation.
- Preserve S:W:H:E evidence where the active Aegis profile requires it.
- Run focused tests, `git diff --check`, and the applicable Aegis/guard checks before handoff.
- Do not claim a live check passed from a sandbox that cannot observe the relevant namespace.

## Taskmaster Transition Policy

`.taskmaster/` is a historical compatibility surface for the completed legacy backlog.

- Do not run `task-master init`.
- Do not create, expand, reprioritize, or update Taskmaster tasks for new work.
- Do not duplicate a Gas City bead into Taskmaster.
- Do not regenerate the repository-wide Taskmaster task files during normal bead work.
- `python3 scripts/codex-task taskmaster health` is read-only and may be used only when
  maintaining legacy compatibility or migrating the old graph.

The Claude/Aegis strict adapter still contains Taskmaster-backed readiness checks. Until that
implementation is migrated and tested, treat it as an explicit legacy compatibility boundary:
do not edit Taskmaster merely to make a new bead-based task appear valid, and do not claim the
adapter is beads-native. Track the adapter migration as bead work and change documentation,
runtime checks, fixtures, and tests together.

## Reboot and Live-Infrastructure Work

Reboot hardening is normal bead work, but applying it may cross host, Windows, WSL, systemd,
signing, or lifecycle boundaries.

- Read-only doctors and artifact preparation may proceed within normal implementation scope.
- Scheduled tasks, service enable/disable, stale-unit cleanup, ACL changes, key operations,
  supervisor restarts, and reboot drills require explicit bounded authority.
- Make recovery deterministic: report which layer failed (Desktop config, WSL boot, user
  systemd, supervisor, store, signer, or worker) rather than applying broad repair.

---

Gas City beads are the single work ledger for new activity; Taskmaster remains historical
until its remaining runtime coupling is deliberately removed.
