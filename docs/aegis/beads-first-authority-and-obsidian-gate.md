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

Record first, change second, gate last. Routine edits go to the passive ledger and human worklog;
they do not trigger an Obsidian rebuild. Projection happens at a useful boundary.

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

The gate blocks when ownership, inventory, hashes, source freshness, work authority, or required
work-item presence disagrees. It does not close a bead, mutate Git, write a worklog, repair a
vault, or run after each source edit.

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

The projection contains no daemon and no in-memory authority. After WSL or Windows restarts:

1. verify Gas City and the ledger through their normal readiness surfaces;
2. export/read the current bead snapshot through the reviewed host path;
3. run `aegis vault gate --phase readiness`;
4. rebuild only if the gate reports stale or missing managed output;
5. rerun the gate and continue.

Because the adapter consumes normalized JSON/JSONL and not a private Beads database API, Gas City
or Beads upgrades can change their implementation without changing this contract. A source-format
change fails closed in the adapter tests before any vault replacement.

## Explicit non-goals

- no Obsidian-to-beads synchronization;
- no Taskmaster and bead dual writes;
- no model-authored claim that substitutes for ledger or Git evidence;
- no per-command or per-mutation vault gate;
- no overwrite of unknown or human-edited vault content;
- no implicit title/label/description/assignee replication without the content-policy opt-in.
