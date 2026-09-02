# Cross-project continuity contract

The continuity auditor separates project identity from ledger identity. A registered project is a
canonical Git root and derived evidence surface. A Bead store is identified by its rig; more than
one project may intentionally share a rig, but the auditor captures that store once and refuses if
the member projects disagree about its bytes.

## Frozen input and deterministic views

`continuity.py snapshot` performs only read-only queries. It validates every registered root with
`project_context.py`, reads each unique rig through `gc bd list --all --limit 0 --json`, projects
only classification fields (never Bead descriptions, notes, acceptance text, or comments), enumerates
managed Git worktrees and branches, reads open GitHub PRs, lifecycle transaction journals,
managed-signing v2 receipts, structured follow-ups, and the installed Obsidian registry/state. It
contains no current-time field. Each rig appears once under `ledgers`; projects reference it by rig.
Equal observed state therefore produces byte-identical JSON.

Each project Git surface includes one canonical-root observation derived without a fetch: exact
path and HEAD, branch or detached state, the descriptor's `base_ref` (or the local
`refs/remotes/origin/HEAD`, falling back to local `refs/remotes/origin/main`), resolved target
commit, ahead/behind counts, and tracked cleanliness. A missing target is unobservable and blocks.
A checkout currently on the target branch blocks when ahead or behind; a deliberate non-target
branch and tracked dirt remain bounded warnings so operator-owned HPFetcher and Blog workspaces are
visible but never rewritten. Omitting this record also blocks, preventing older or hand-built
snapshots from silently claiming canonical-root coverage.

Snapshot v2 also captures one city-global runtime parity surface. The native session side comes
from the structured `gc session list --json` API and excludes volatile timestamps and output. The
host side scans only same-UID procfs for stable session-leading `tmux -L city` servers, recognizing
both bare and absolute `argv[0]`, and records PID, SID, PPID, UID, kernel start ticks, cmdline digest,
and sorted child PIDs. Stat, cmdline, and child membership must all survive a stable reread. It never
opens the tmux socket, reads process environments, or changes a
process. A same-UID visibility or stable-reread failure is `unknown` and blocks acceptance; it is
never rewritten as absence. A server without a native tmux session is runtime residue, a native
tmux session without a server is missing runtime, and multiple servers are split-brain. Historical
v1 snapshots remain auditable with an explicit non-blocking `city-runtime-not-captured` warning.

Obsidian continuity is not one Boolean. The snapshot preserves four independent facts:

- filesystem projection status and the completed reconciliation time;
- the registry-cycle state, derived from the reconciler's read-only flock observation;
- live-index status, host IPC authority, and observation time; and
- WSL Obsidian process state from the user systemd manager, including the matching scope identity.

The reconciler holds one registry-wide lock and stages a candidate as `pending_success`, retaining
the prior fully observed `last_success` until batched IPC completes. A snapshot taken mid-cycle is
therefore deterministic and explicitly `running`, not falsely stale. A pending candidate without
the lock is `interrupted` and blocks acceptance. If the user systemd manager is not observable from
the caller's namespace, process state is `unknown` and produces a warning; it is never rewritten as
`absent`. Actual absent or inactive scope evidence remains an error. The observer never starts,
stops, restarts, or signals Obsidian.

The reconciler-owned continuity dashboard is the one bounded exception to live lock observation.
It captures a post-release candidate with `snapshot --obsidian-cycle-status idle` only after every
project candidate has passed its filesystem and live-index gates. The CLI accepts no other explicit
status. This keeps the dashboard byte-identical to the immediately subsequent strict check after the
registry lock is released, while ordinary callers that omit the option continue to observe a real
mid-cycle `running` state and an abandoned pending candidate as `interrupted`.

The JSON audit and human status view are both derived by `continuity_model.py`. `next_actions` is
the sole source for the human `next` lines. If any Bead store contains an `initiative:active` epic,
only that epic and its transitive `parent-child` descendants populate Current/Next/Blocked; other
stores remain coverage and orphan-detection surfaces. This prevents historical backlogs from
silently becoming the active plan.

```bash
python3 plugins/gas-city-workflow/scripts/continuity.py snapshot \
  --output /path/to/frozen-snapshot.json
python3 plugins/gas-city-workflow/scripts/continuity.py audit \
  --snapshot /path/to/frozen-snapshot.json
python3 plugins/gas-city-workflow/scripts/continuity.py status \
  --snapshot /path/to/frozen-snapshot.json
```

Descriptor-only future projects are explicit inputs, not filesystem guesses:

```bash
python3 plugins/gas-city-workflow/scripts/continuity.py snapshot \
  --project-root /absolute/canonical/project-root
```

The root must pass the same descriptor, Git-common-directory, remote identity, and approved
worktree-root checks as every established project. Repeating a registered root is a no-op;
colliding roots or IDs fail closed.

## Findings and retained evidence

The auditor does not call preserved journals or signing receipts residue merely because their Bead
is closed. Those are append-only evidence. It does flag:

- managed branches, worktrees, open PRs, active Aegis trackers, lifecycle transactions, or signing
  receipts whose Bead does not exist in the selected rig;
- active trackers and open PRs bound to closed work;
- worktrees or branches left by conclusively terminal generated work;
- untracked, missing, split-brain, or unobservable city tmux runtime relative to the native session
  ledger;
- missing or unresolved canonical-root observations, and a target-branch checkout that is ahead of
  or behind its existing local target ref;
- projects missing from the Obsidian registry, stale filesystem projections, or unconfirmed live
  index observations, including a registry entry whose project ID disagrees with the canonical
  project descriptor; and
- a promised follow-up that has neither a real Bead nor an explicit disposition.

Projects record promises in `.gas-city-workflow/followups.json` using
`config/followups.schema.json`. Prose is not parsed and chat memory is never evidence. Historical
Taskmaster ACTIVE folders are identified as legacy warnings rather than fabricated Beads.

Historical branches and worktrees that must remain as evidence use the tracked
`config/continuity-residue-dispositions.json` contract. A disposition is not an allowlist or a
cleanup bypass: it binds one project, surface, identity, Bead candidate, exact commit, required
clean worktree state, reason, and independently verified merge or file-digest evidence. Exact
matches remain visible as non-blocking `preserved-*` warnings. A missing artifact, changed HEAD,
dirty worktree, invalid evidence, redundant disposition, or other mismatch fails closed. Removing
or changing preserved history therefore requires an explicit append-forward disposition update;
the auditor never infers that history is safe to erase.

Exit `0` means the report is internally complete and has no error finding. Exit `3` means the
snapshot was valid but current cross-surface drift blocks acceptance. Exit `2` means the snapshot
or a provider contract was invalid.

Raw snapshots can contain project task titles even though content fields are excluded. Treat them
as local evidence: publish the canonical report/status and the snapshot digest, not the raw snapshot,
unless the destination's disclosure boundary has been reviewed separately.
