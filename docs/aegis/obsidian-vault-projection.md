# Aegis Derived Obsidian Vault

## Status

The Gas City cutover moves the existing read-only, disposable Obsidian-compatible projection to
authoritative Beads/Dolt task data. The vault is a knowledge view, not a workflow database and
not a replacement for Beads/Dolt, Git, the passive ledger, the computed capsule, the delivery
witness, or preserved S:W:H:E narrative.

The authority chain is:

```text
Git + Beads/Dolt + passive ledger + capsule + witness + preserved legacy narrative
                                    |
                                    v
                     deterministic Obsidian projection
```

Nothing in the vault is read back into Aegis. Editing a generated note has no effect on task,
delivery, policy, or repository state, and the next build refuses to overwrite that edit rather
than silently discarding it.

Task collection executes exactly:

```text
bd --readonly -C <repository> export
```

The selected executable is resolved once, opened without following a final symlink, rejected if
it is not executable or is group/world writable, hashed, and then invoked through that exact open
file descriptor. Production passes both its absolute path and SHA-256 pin. A strict Beads 1.1.0
version check and read-only `HASHOF('main')` query surround the export; a changed or ambiguous
Dolt head stops the build. The manifest records the executable path, executable digest, version,
raw export digest, and attested Dolt head.

The default export intentionally excludes infrastructure records and memories; neither belongs
in the project-task projection. The JSONL is parsed from stdout. A missing or changed `bd`, a
non-zero exit, malformed or duplicate-key JSON, duplicate issue records, invalid typed
relationships, unsafe IDs, duplicate migration aliases, or a configured limit violation stops
collection before any vault replacement. The generator never reads
`.taskmaster/tasks/tasks.json` and has no Taskmaster fallback.

## Commands

```bash
# Resolve the default path beside the out-of-worktree ledger.
aegis vault path --target-dir .

# Build or refresh atomically with the production Beads pin.
aegis vault build --target-dir . \
  --bd-executable "$HOME/gas-city/bin/bd" \
  --expected-bd-sha256 f7dcf3d22eae0bf09d764a9a47ab5c6e263ee91b19f2243d9e0e077561cceb1e

# Verify ownership, exact inventory, hashes, and source freshness.
aegis vault check --target-dir . \
  --bd-executable "$HOME/gas-city/bin/bd" \
  --expected-bd-sha256 f7dcf3d22eae0bf09d764a9a47ab5c6e263ee91b19f2243d9e0e077561cceb1e

# Use a deliberate out-of-repository destination.
aegis vault build --target-dir . --output /safe/path/project-aegis-vault
```

The default is:

```text
${XDG_STATE_HOME:-~/.local/state}/aegis/<repository-key>/obsidian-vault
```

The generator rejects any output inside the source repository. The vault therefore cannot make
the product worktree dirty, enter a pull request accidentally, or become a competing tracked
state surface.

## Graph Model

Generated Markdown notes use deterministic YAML properties and path-qualified wikilinks. The
first implementation emits:

- one bounded orientation note;
- one task note per exported Bead, keyed and named by the canonical Bead ID;
- outbound and inbound typed relationships, including `blocks` and `parent-child` edges;
- session, branch, agent, and worktree nodes observed in high-signal ledger events;
- witness, verification, delivery, task-truth, operator-authority, risk, and tool-failure
  evidence notes;
- structural inventory notes for preserved session, plan, tracker, implementation, changelog,
  decision, finding, and handoff documents;
- activity and evidence indexes;
- `.base` views for tasks, evidence, and legacy documents.

Obsidian turns internal links into graph edges; Properties provide typed note metadata; Bases
provide table views over those properties. The projection uses only those native formats, so it
does not install or require an Obsidian plugin:

- [Obsidian internal links](https://obsidian.md/help/links)
- [Obsidian Properties](https://obsidian.md/help/properties)
- [Obsidian Bases](https://obsidian.md/help/bases)
- [Obsidian Graph view](https://obsidian.md/help/plugins/graph)

The output deliberately does not generate `.obsidian/`, prescribe a theme, or modify a user's
Obsidian settings.

Beads status values are normalized to lowercase snake case and priority remains the native
integer `0`–`4` (`P0` is highest). `issue_type` and every relationship type remain explicit
properties or headings. IDs use a total natural ordering, so a single export may safely contain
numeric, dotted, and prefixed Bead IDs without comparison failures or nondeterministic output.

During the one-time migration, an exact `external_ref` of
`taskmaster:master:<numeric-or-dotted-id>` contributes a non-authoritative Taskmaster alias.
That alias may connect legacy numeric task references, capsule orientation, and historical ledger
events to the canonical Bead note. No other field or approximate external reference creates an
alias, and duplicate aliases fail closed.

## Context And Output Budget

The ledger can contain tens of thousands of low-level mutation and gate events. Turning every
row into a note would create an unusable graph and would cause every read-only hook invocation to
make the vault stale. Therefore:

- only high-signal lifecycle, scope, task, risk, verification, witness, delivery, authority, and
  failure events affect the graph;
- mutation and gate-decision rows remain queryable in the ledger but are not expanded into notes;
- a deduplicated identity edge set (agent, parent, session, branch, and worktree) is derived from
  all rows, so repeated low-level calls do not churn the graph while genuinely new topology is
  visible;
- event metadata is allowlisted and clipped;
- raw command strings are never copied;
- evidence, Bead, session, branch, agent, worktree, and legacy-document counts have hard limits
  (the legacy ceiling is 5,000 after source-repository dogfood measured 2,175 real documents);
- a limit violation fails before replacing a current vault.

This is an LLM-context design constraint as much as an Obsidian usability decision: navigating
the view must never dump the raw flight recorder into an agent's context window.

## Legacy Coexistence

Legacy workflow files remain valuable because they contain decisions, plans, narrative,
trade-offs, and failure context that cannot be reconstructed reliably from tool telemetry. The
vault inventories their human-authored content outside Aegis generated-marker blocks and links it
to matching task nodes. It records:

- repository-relative source path;
- document kind;
- byte size;
- human-authored nonblank line count;
- heading sample;
- checkbox and S:W:H:E counts;
- generated-block count;
- deterministic content digest;
- related task IDs.

It does **not** copy the full prose by default. The repository document remains the narrative
authority. This makes unique legacy content measurable without turning the vault into an
uncontrolled duplicate or leaking arbitrary historical text into another storage surface.

The coexistence rule remains:

- ledger/capsule/witness own observed current truth and delivery proof;
- legacy S:W:H:E files retain or receive human narrative and durable handoff context;
- the vault supplies navigation and cross-surface relationships;
- no legacy surface is demoted or retired merely because a vault note exists.

## Safety And Atomicity

Every generated vault contains `.aegis-vault.json`, which declares the generator, source digest,
source HEAD, exact owned-file inventory, and SHA-256 hash of every generated file.

Before rebuilding, Aegis requires:

1. the directory is not a symlink;
2. the manifest identifies an Aegis-owned generated root;
3. the actual inventory exactly matches the manifest;
4. every owned file still matches its hash;
5. no unknown/manual file has appeared.

The complete next vault is written to a sibling staging directory and self-checked. Directory
replacement uses same-filesystem atomic renames, with the previous valid vault retained as a
rollback target until the replacement succeeds. Removed Beads therefore remove their generated
notes as part of the same exact-inventory replacement; individual stale notes are never deleted
in place. A byte-identical source snapshot is a no-op.

The generator never:

- writes the source repository;
- appends ledger rows;
- updates Beads or Dolt;
- compiles or rewrites the capsule;
- invokes GitHub;
- drains pending evidence;
- deletes or overwrites unknown files;
- follows output symlinks;
- imports changes from Obsidian.

## Privacy

Ledger capture-time redaction remains the first defense. The vault adds a second bounded
projection layer:

- only an allowlist of event metadata is rendered;
- raw commands and arbitrary `extra` payloads are omitted;
- common bearer, GitHub, OpenAI-style, and JWT token shapes are redacted;
- worktree and agent note filenames use fingerprints;
- legacy documents contribute structure and hashes, not full body text.

The generated vault still contains project and workflow metadata. Operators should protect its
XDG state directory with the same care as the ledger.

## Validation Contract

Acceptance requires:

- two builds over the same authoritative input are byte-identical and the second is a no-op;
- task collection executes a SHA-256-pinned Beads 1.1.0 file descriptor, attests one unchanged
  Dolt `main` head around the exact read-only `export`, and has no Taskmaster fallback or
  infrastructure/memory inclusion;
- canonical note identity is the Bead ID, with Taskmaster aliases derived only from exact
  migration `external_ref` values;
- `blocks`, `parent-child`, and other typed export relationships remain distinguishable in both
  directions;
- malformed JSONL, duplicate IDs or aliases, invalid relationships, and unavailable Beads fail
  before replacing a current vault;
- mixed numeric, dotted, and prefixed Bead IDs sort deterministically;
- additional low-level gate/mutation traffic does not churn the graph;
- a new high-signal event changes the source digest;
- links connect tasks, sessions, branches, agents, worktrees, evidence, and legacy documents;
- in-repository, symlinked, unknown, or tampered outputs fail closed;
- a failed staged build leaves the previous valid vault intact;
- removing a Bead removes its generated note through exact atomic replacement;
- source files remain byte-identical;
- `aegis vault check` detects stale or modified output without writing;
- realistic Blog and HP-Fetcher event volumes remain within the documented bounds.

## Non-Goals

This slice does not:

- create, update, close, migrate, or reconcile Beads;
- read Taskmaster as a task source or silently fall back to it;
- replace the legacy S:W:H:E workflow;
- implement vault-to-repository writeback;
- install Obsidian or the Kepano Obsidian skills;
- publish a multi-user knowledge service;
- treat the graph as proof of policy compliance.

Those decisions remain separate and require their own reviewed authority boundary.
