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
- projects missing from the Obsidian registry, stale filesystem projections, or unconfirmed live
  index observations, including a registry entry whose project ID disagrees with the canonical
  project descriptor; and
- a promised follow-up that has neither a real Bead nor an explicit disposition.

Projects record promises in `.gas-city-workflow/followups.json` using
`config/followups.schema.json`. Prose is not parsed and chat memory is never evidence. Historical
Taskmaster ACTIVE folders are identified as legacy warnings rather than fabricated Beads.

Exit `0` means the report is internally complete and has no error finding. Exit `3` means the
snapshot was valid but current cross-surface drift blocks acceptance. Exit `2` means the snapshot
or a provider contract was invalid.

Raw snapshots can contain project task titles even though content fields are excluded. Treat them
as local evidence: publish the canonical report/status and the snapshot digest, not the raw snapshot,
unless the destination's disclosure boundary has been reviewed separately.
