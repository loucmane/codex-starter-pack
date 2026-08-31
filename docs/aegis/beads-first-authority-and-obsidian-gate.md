---
tags:
  - aegis
  - gas-city
  - beads
  - obsidian
authority: design-contract
bead: ga-zbmk
---

# Beads-first authority and Obsidian gate

> [!summary]
> Gas City beads answer *what work exists and its lifecycle state*. Git and delivery evidence
> answer *what shipped*. The passive Aegis ledger answers *what was observed*. Obsidian makes
> those sources navigable and durable, but never writes truth back to them.

## The operating model

```text
operator/agent
    |
    +--> Gas City bead (current work authority)
    +--> Git branch/commit (source truth)
    +--> Aegis ledger events (observed evidence)
    +--> witness/CI/receipt (delivery truth)
              |
              v
       normalized Aegis snapshot
              |
              v
     managed Obsidian Aegis subtree
```

Taskmaster remains readable for historical repositories, but it is not allocated alongside a
bead. Supplying `--beads-json` is the explicit authority selection and replaces Taskmaster in that
snapshot.

## S:W:H:E in the beads-first workflow

One compact line records each meaningful boundary:

```text
[S:<session>|W:<bead>|H:<validated-handler>|E:<checkable-evidence>]
```

- `S` is the live session or stable resume lineage.
- `W` is the exact claimed bead, such as `ga-zbmk`; do not use a title or infer it from prose.
- `H` is the validated logical handler or workflow step, not an arbitrary shell fragment.
- `E` is independently checkable: a ledger event, commit, receipt, report, PR, or bounded path.

Record first, change second, gate last. Routine edits go to the passive ledger and human worklog.
The user-scoped reconciler coalesces those changes into a bounded periodic rebuild; the strict
readiness, closeout, and publication gates remain the synchronous workflow boundaries.

## Obsidian ownership

The WSL vault is `/home/loucmane/vaults/main`.

| Tree | Writer | Purpose |
| --- | --- | --- |
| `GasCity/<project>/Tasks/` | Gas City vault projector | Structured bead projection |
| `GasCity/<project>/Docs/worklogs/` | Task agents/operators | Findings, decisions, progress, handoff |
| `GasCity/<project>/Aegis/` | Aegis vault generator | Ledger/evidence graph and compatibility links |
| Everything else | Human owner | Curated knowledge |

The Aegis generator receives the exact `Aegis/` subtree as `--output`. It never receives the
vault root or a project root containing human files.

## Boundary gates

Use the same frozen bead snapshot and content policy for build and gate:

```bash
aegis vault build \
  --target-dir /path/to/repository \
  --beads-json /owner/evidence/current-beads.json \
  --output /home/loucmane/vaults/main/GasCity/<project>/Aegis

aegis vault gate \
  --phase closeout \
  --target-dir /path/to/repository \
  --beads-json /owner/evidence/current-beads.json \
  --output /home/loucmane/vaults/main/GasCity/<project>/Aegis
```

Because the build swaps the managed subtree atomically, Obsidian's Windows-side watcher may
retain its prior WSL index. After a successful filesystem gate, a host operator may run
`obsidian vault=main reload` and repeat the managed-note read. Do not put this mutation in the
read-only doctor, and do not reinterpret a stale index as evidence that the desktop app is
closed.

The gate blocks when ownership, inventory, hashes, source freshness, work authority, or required
work-item presence disagrees. It does not close a bead, mutate Git, write a worklog, repair a
vault, or run after each source edit.

## Automatic freshness

`aegis-obsidian-reconcile.timer` runs the installed, deterministic publisher after WSL user
systemd starts and then once per minute. Its registry names every project, repository, exact bead
export command, output subtree, content policy, and freshness SLA. There is no implicit project or
bead-store discovery.

Each run takes a non-blocking per-project lock, exports a size-bounded snapshot, reads the passive
ledger without writing it, and builds through the existing atomic vault generator. Byte-identical
input is a no-op. A failed export, parse, limit check, or staged publication retains the previous
valid subtree and records a bounded error in the user-private state directory. Readiness runs the
installed `check` command, which re-derives the current source digest; an old success timestamp by
itself can never hide stale beads.

The passive ledger uses SQLite WAL mode while agent hooks are active. The hardened reconciler keeps
`ProtectHome=read-only`: it never grants the timer write access to the evidence store merely so
SQLite can coordinate a reader. Instead, it copies only the regular database and WAL files into a
private writable temporary directory, proves the source pair remained byte-stable across the copy,
and lets SQLite rebuild transient `-shm` state there. The snapshot is size-bounded and retry-bounded;
symlinks, non-regular components, oversized input, or a continuously changing pair fail closed while
the last good vault remains intact.

Adding HPFetcher, Blog, or a new project is a registry change plus a deterministic unit refresh—not
a second service or a copied script. The host registry binds the project's exact absolute rig root;
it is never inferred from the rig ID. The refresh extends the unit's write allowlist only to the new
output's existing parent. The timer remains one host-side controller and each project retains a
disjoint Aegis-owned output subtree.

## Observer authority

The filesystem projection and the Obsidian desktop process are different evidence surfaces.
Vault build/check/gate results are authoritative for the managed subtree and remain valid when
the GUI is closed. Live Obsidian CLI reachability is only a host-WSL smoke over those bytes.

Every environment-sensitive observation records both its observer and its authority:

| Observer | May prove | Must not infer from an empty or denied result |
| --- | --- | --- |
| `codex-sandbox` / worker namespace | its own files, Git state, bead/receipt surfaces granted to it | host process absence, cross-UID service state, systemd state, Windows interop, Obsidian IPC state |
| `host-wsl` | systemd/cgroup/service state, host process trees, local service sockets, live Obsidian CLI | Windows facts not returned by the approved interop probe |
| filesystem vault gate | managed output ownership, inventory, hashes, and source freshness | whether the Obsidian GUI is currently open |

Observer-limited negatives are `UNKNOWN`, not `FAIL` and not proof of absence. A positive
sandbox observation may be retained, but an authoritative negative must be re-run from the
declared host observer.

Existing projects adopt this without rewriting their history: bind current work to the native
project bead, keep Git as source truth, install/register the project-local Aegis adapter, assign
one owned `GasCity/<project>/Aegis/` subtree, and pass one filesystem gate plus one host-WSL
live-app smoke. New projects receive those defaults during initialization. Taskmaster remains
historical compatibility only; no bead/Taskmaster dual write is introduced.

## Reboot and upgrade behavior

The projection contains no in-memory authority. The persistent user timer re-arms after WSL or
Windows restarts, including missed-run reconciliation through `Persistent=true`. The readiness
doctor requires the installed source-current check to pass; a stopped timer, stale source digest,
or recorded publication failure is visible rather than silently leaving yesterday's vault in
place. Manual `vault gate` remains available as the exact workflow boundary and recovery proof.

Because the adapter consumes normalized JSON/JSONL and not a private Beads database API, Gas City
or Beads upgrades can change their implementation without changing this contract. A source-format
change fails closed in the adapter tests before any vault replacement.

## Explicit non-goals

- no Obsidian-to-beads synchronization;
- no Taskmaster and bead dual writes;
- no model-authored claim that substitutes for ledger or Git evidence;
- no per-command or per-mutation vault gate (changes are debounced by one bounded host timer);
- no overwrite of unknown or human-edited vault content;
- no implicit title/label/description/assignee replication without the content-policy opt-in.
