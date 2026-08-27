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
